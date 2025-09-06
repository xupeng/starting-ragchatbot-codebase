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
                
                # 记录来源信息，包含链接
                source = {
                    'text': course_title,
                    'link': None
                }
                
                if lesson_num is not None:
                    source['text'] += f" - 第 {lesson_num} 章节"
                    # 获取lesson链接
                    lesson_link = self.store.get_lesson_link(course_title, lesson_num)
                    if lesson_link:
                        source['link'] = lesson_link
                
                sources.append(source)
                
                # 组合结果
                formatted_results.append(f"{header}\n{doc}")
            
            # 存储来源信息供后续使用
            self.last_sources = sources
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            error_msg = f"搜索功能出现异常: {str(e)}"
            return error_msg
    
    def get_course_outline(self, course_title: str) -> str:
        """
        获取指定课程的完整大纲信息。
        
        这个函数用于查找课程的完整大纲，包括课程标题、链接和所有课程的详细信息。
        
        Args:
            course_title: 课程名称或关键词（支持部分匹配，如'MCP'、'Chroma'等）
            
        Returns:
            格式化的课程大纲字符串，包含课程标题、链接和完整的课程列表
        """
        
        try:
            # 获取所有课程元数据
            all_courses = self.store.get_all_courses_metadata()
            
            if not all_courses:
                return "当前系统中没有找到任何课程信息。"
            
            # 查找匹配的课程（支持部分匹配）
            matching_course = None
            course_title_lower = course_title.lower().strip()
            
            for course_meta in all_courses:
                course_name = course_meta.get('title', '')
                if course_title_lower in course_name.lower():
                    matching_course = course_meta
                    break
            
            if not matching_course:
                # 如果没有找到精确匹配，尝试模糊匹配
                for course_meta in all_courses:
                    course_name = course_meta.get('title', '')
                    # 检查课程标题中是否包含查询关键词的任何单词
                    query_words = course_title_lower.split()
                    if any(word in course_name.lower() for word in query_words if len(word) > 2):
                        matching_course = course_meta
                        break
            
            if not matching_course:
                available_courses = [meta.get('title', 'Unknown') for meta in all_courses]
                return f"未找到与 '{course_title}' 匹配的课程。\n\n可用课程：\n" + "\n".join(f"- {title}" for title in available_courses)
            
            # 构建课程大纲响应
            course_name = matching_course.get('title', 'Unknown Course')
            course_link = matching_course.get('course_link', None)
            course_instructor = matching_course.get('instructor', 'Unknown Instructor')
            lessons = matching_course.get('lessons', [])
            
            # 格式化响应
            outline_parts = []
            outline_parts.append(f"【课程大纲】{course_name}")
            outline_parts.append(f"教师：{course_instructor}")
            
            if course_link:
                outline_parts.append(f"课程链接：{course_link}")
            
            if lessons:
                outline_parts.append(f"\n课程内容（共 {len(lessons)} 个课程）：")
                for lesson in lessons:
                    lesson_num = lesson.get('lesson_number', 'N/A')
                    lesson_title = lesson.get('lesson_title', 'Unknown Lesson')
                    lesson_link = lesson.get('lesson_link', '')
                    
                    lesson_line = f"课程 {lesson_num}: {lesson_title}"
                    if lesson_link:
                        lesson_line += f" - {lesson_link}"
                    outline_parts.append(lesson_line)
            else:
                outline_parts.append("\n暂无详细课程信息。")
            
            # 存储来源信息
            self.last_sources = [{
                'text': course_name,
                'link': course_link
            }]
            
            return "\n".join(outline_parts)
            
        except Exception as e:
            error_msg = f"获取课程大纲时出现异常: {str(e)}"
            return error_msg

    def get_last_sources(self) -> list:
        """获取最后一次搜索的来源信息"""
        return self.last_sources.copy()
    
    def reset_sources(self):
        """重置来源信息"""
        self.last_sources = []