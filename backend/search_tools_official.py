from typing import Optional
from vector_store import VectorStore, SearchResults


class OfficialSearchManager:
    """官方Gemini API的搜索管理器 - 使用纯Python函数"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # 跟踪最后搜索的来源
    
    def search_course_content(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        搜索课程材料内容。
        
        这个函数用于查找与特定查询相关的课程内容。可以通过课程名称和章节编号进一步筛选结果。
        
        Args:
            query: 要搜索的内容关键词
            course_name: 可选的课程名称筛选（支持部分匹配，如'MCP'、'Chroma'等）
            lesson_number: 可选的特定章节编号筛选（如1、2、3等）
            
        Returns:
            格式化的搜索结果字符串，包含相关的课程内容
        """
        
        try:
            # 使用向量存储进行搜索
            results = self.store.search(
                query=query,
                course_name=course_name,
                lesson_number=lesson_number
            )
            
            # 处理搜索错误
            if results.error:
                return f"搜索时出现错误: {results.error}"
            
            # 处理空结果
            if results.is_empty():
                filter_info = ""
                if course_name:
                    filter_info += f" 在课程 '{course_name}' 中"
                if lesson_number:
                    filter_info += f" 在第 {lesson_number} 章节中"
                return f"未找到与 '{query}' 相关的内容{filter_info}。"
            
            # 格式化搜索结果
            formatted_results = []
            sources = []
            
            for doc, meta in zip(results.documents, results.metadata):
                course_title = meta.get('course_title', '未知课程')
                lesson_num = meta.get('lesson_number')
                
                # 构建结果头部
                header = f"【{course_title}"
                if lesson_num is not None:
                    header += f" - 第 {lesson_num} 章节"
                header += "】"
                
                # 记录来源信息
                source = course_title
                if lesson_num is not None:
                    source += f" - 第 {lesson_num} 章节"
                sources.append(source)
                
                # 组合结果
                formatted_results.append(f"{header}\n{doc}")
            
            # 存储来源信息供后续使用
            self.last_sources = sources
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            error_msg = f"搜索功能出现异常: {str(e)}"
            return error_msg
    
    def get_last_sources(self) -> list:
        """获取最后一次搜索的来源信息"""
        return self.last_sources.copy()
    
    def reset_sources(self):
        """重置来源信息"""
        self.last_sources = []