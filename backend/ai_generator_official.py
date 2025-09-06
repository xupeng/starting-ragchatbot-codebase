from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any, Callable
import logging
import os


class OfficialGeminiGenerator:
    """使用官方Google Gemini API的AI生成器"""
    
    def __init__(self, api_key: str, model: str):
        # 验证输入参数
        if not api_key or api_key.strip() == "":
            raise ValueError("API Key 不能为空。请在 .env 文件中设置 GEMINI_API_KEY")
        
        if not model or model.strip() == "":
            raise ValueError("Model 不能为空。请在 .env 文件中设置 GEMINI_MODEL")
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化官方Gemini客户端
        try:
            # 设置环境变量（官方SDK会自动读取）
            os.environ['GEMINI_API_KEY'] = api_key.strip()
            
            # 初始化客户端
            self.client = genai.Client()
            self.model = model.strip()
            
            self.logger.info(f"官方Gemini AI生成器初始化成功 - 模型: {self.model}")
            
        except Exception as e:
            self.logger.error(f"初始化官方Gemini客户端失败: {e}")
            raise ValueError(f"无法初始化官方Gemini客户端: {e}")
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         search_function: Optional[Callable] = None) -> str:
        """
        使用官方Gemini API生成响应，支持自动函数调用
        
        Args:
            query: 用户的问题或请求
            conversation_history: 之前的对话历史
            search_function: 可用的搜索函数
            
        Returns:
            生成的响应文本
        """
        
        # 构建系统提示词
        system_prompt = """你是一个专业的课程材料助手。当用户询问关于课程内容、大纲、章节或教育材料的问题时，你应该使用search_course_content函数来查找相关信息。

重要指导原则：
- 对于课程相关问题（如课程大纲、内容、章节等），总是先使用搜索工具
- 基于搜索结果提供准确、有用的回答
- 保持回答简洁明了
- 对于一般对话（如问候），直接回答即可

请根据用户的问题提供帮助。"""
        
        # 构建内容
        full_prompt = system_prompt
        if conversation_history:
            full_prompt += f"\n\n历史对话:\n{conversation_history}"
        full_prompt += f"\n\n用户问题: {query}"
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=full_prompt)]
            )
        ]
        
        # 配置生成参数
        config_kwargs = {}
        if search_function:
            # 使用自动函数调用
            config_kwargs["tools"] = [search_function]
        
        config = types.GenerateContentConfig(**config_kwargs)
        
        # 发送API请求
        try:
            self.logger.info(f"🚀 发送官方Gemini API请求")
            self.logger.info(f"   模型: {self.model}")
            
            if search_function:
                self.logger.info(f"   包含搜索工具: {search_function.__name__}")
            
            # 记录查询预览
            query_preview = query[:100] if len(query) > 100 else query
            self.logger.info(f"   用户查询: {query_preview}...")
            
            # 调用官方API
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            self.logger.info(f"✅ 成功收到官方Gemini API响应")
            
            # 获取响应文本
            response_text = response.text if response.text else ""
            
            self.logger.info(f"   响应长度: {len(response_text)} 字符")
            
            return response_text
            
        except Exception as e:
            # 详细错误日志
            error_msg = f"官方Gemini API请求失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.logger.error(f"   异常类型: {type(e).__name__}")
            
            # 常见错误提示
            if "API_KEY" in str(e) or "authentication" in str(e).lower():
                error_msg += "\n💡 请检查GEMINI_API_KEY是否正确设置"
                error_msg += "\n💡 获取API密钥: https://aistudio.google.com/app/apikey"
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                error_msg += "\n💡 可能的原因: API配额不足或请求频率限制"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                error_msg += "\n💡 可能的原因: 网络连接问题"
            
            raise RuntimeError(error_msg)