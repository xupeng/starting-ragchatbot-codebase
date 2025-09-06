from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any, Callable
import logging


class GeminiAIGenerator:
    """Handles interactions with Gemini API for generating responses"""
    
    # Static system prompt
    SYSTEM_PROMPT = """你是一个课程材料数据库的AI助手。对于任何关于课程材料、主题或教育内容的问题，你必须使用search_course_content工具。

重要指令：
1. **对于以下类型的问题，总是先使用搜索工具**：
   - 课程内容、大纲或主题
   - 课程详情或特定信息
   - 教育材料或课程中的概念
   - 课程涵盖或包含的内容

2. **工具使用规则**：
   - 使用相关的查询词调用search_course_content
   - 如果提到课程名称，包含course_name参数（如"MCP"、"Chroma"、"Anthropic"）
   - 如果指定了课程章节，包含lesson_number参数
   - 每次响应最多使用一次搜索

3. **响应格式**：
   - 基于搜索结果提供直接答案
   - 保持回答简洁和教育性
   - 包含找到内容中的具体示例
   - 不要提及搜索过程

4. **仅在一般对话（如问候、感谢等）时不搜索**

记住：如果问题涉及课程或学习材料，你必须先搜索。"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        # 验证输入参数
        if not api_key or api_key.strip() == "":
            raise ValueError("API Key 不能为空。请在 .env 文件中设置 GEMINI_API_KEY")
        
        if not model or model.strip() == "":
            raise ValueError("Model 不能为空。请在 .env 文件中设置 GEMINI_MODEL")
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Gemini 客户端
        try:
            # 配置客户端
            client_config = {"api_key": api_key.strip()}
            
            # 对于自定义端点，使用http_options
            if base_url and not base_url.startswith("https://generativelanguage.googleapis.com"):
                # 暂时不支持自定义端点，使用默认配置
                self.logger.warning(f"自定义端点 {base_url} 可能不被支持，使用默认Gemini API端点")
            
            self.client = genai.Client(**client_config)
            self.model = model.strip()
            
            self.logger.info(f"Gemini AI 生成器初始化成功 - 模型: {self.model}")
            
        except Exception as e:
            self.logger.error(f"初始化 Gemini 客户端失败: {e}")
            raise ValueError(f"无法初始化 Gemini 客户端: {e}")
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         search_function: Optional[Callable] = None) -> str:
        """
        Generate AI response with optional function calling.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            search_function: The search function to make available to the model
            
        Returns:
            Generated response as string
        """
        
        # 构建系统内容
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\n历史对话:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # 准备内容
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(f"System: {system_content}\n\nUser: {query}")]
            )
        ]
        
        # 准备配置，包含工具（如果提供）
        config_kwargs = {}
        if search_function:
            config_kwargs["tools"] = [search_function]
        
        config = types.GenerateContentConfig(**config_kwargs)
        
        # 发送请求
        try:
            self.logger.info(f"🚀 发送 Gemini API 请求")
            self.logger.info(f"   模型: {self.model}")
            
            if search_function:
                self.logger.info(f"   包含工具: search_course_content")
            
            # 记录查询内容（用于调试）
            query_preview = query[:100] if len(query) > 100 else query
            self.logger.info(f"   用户查询: {query_preview}...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            self.logger.info(f"✅ 成功收到 Gemini API 响应")
            
            # 获取响应文本
            response_text = response.text if response.text else ""
            
            self.logger.info(f"   响应长度: {len(response_text)} 字符")
            
            return response_text
            
        except Exception as e:
            # 详细记录错误信息
            error_msg = f"Gemini API 请求失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.logger.error(f"   异常类型: {type(e).__name__}")
            
            # 提供更具体的错误信息
            if "unauthorized" in str(e).lower() or "401" in str(e):
                error_msg += "\n💡 可能的原因: API Key 无效或权限不足"
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                error_msg += "\n💡 可能的原因: 网络连接问题或服务器超时"
            elif "404" in str(e) or "not found" in str(e).lower():
                error_msg += "\n💡 可能的原因: Base URL 或模型名称错误"
            elif "429" in str(e):
                error_msg += "\n💡 可能的原因: API 请求频率限制"
            elif "500" in str(e):
                error_msg += "\n💡 可能的原因: 服务器内部错误"
            
            raise RuntimeError(error_msg)