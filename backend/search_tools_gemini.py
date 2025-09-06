from typing import Optional
from vector_store import VectorStore, SearchResults


class GeminiSearchTools:
    """Gemini原生函数格式的搜索工具"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # 跟踪最后搜索的来源
    
    def search_course_content(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        搜索课程材料，支持智能课程名称匹配和课程章节筛选。
        
        Args:
            query: 要在课程内容中搜索的内容
            course_name: 课程标题（支持部分匹配，如 'MCP', 'Introduction'）
            lesson_number: 要搜索的特定课程章节编号（如 1, 2, 3）
            
        Returns:
            格式化的搜索结果或错误信息
        """
        
        # 使用向量存储的统一搜索接口
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # 处理错误
        if results.error:
            return results.error
        
        # 处理空结果
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" 在课程 '{course_name}' 中"
            if lesson_number:
                filter_info += f" 在第 {lesson_number} 章节中"
            return f"未找到相关内容{filter_info}。"
        
        # 格式化并返回结果
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """使用课程和章节上下文格式化搜索结果"""
        formatted = []
        sources = []  # 为UI跟踪来源
        
        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            # 构建上下文标题
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - 第 {lesson_num} 章节"
            header += "]"
            
            # 为UI跟踪来源
            source = course_title
            if lesson_num is not None:
                source += f" - 第 {lesson_num} 章节"
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        # 存储来源以供检索
        self.last_sources = sources
        
        return "\n\n".join(formatted)
    
    def get_last_sources(self) -> list:
        """获取最后搜索操作的来源"""
        return self.last_sources
    
    def reset_sources(self):
        """重置来源"""
        self.last_sources = []