import warnings
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import os
import traceback

from config import config
from rag_system import RAGSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
    ]
)

# 设置特定模块的日志级别
logging.getLogger('ai_generator').setLevel(logging.INFO)
logging.getLogger('rag_system').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Course Materials RAG System", root_path="")

# Add trusted host middleware for proxy
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Enable CORS with proper settings for proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize RAG system
rag_system = RAGSystem(config)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None

class SourceItem(BaseModel):
    """Model for a source with optional link"""
    text: str
    link: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Union[str, Dict[str, Optional[str]]]]
    session_id: str

class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]

# API Endpoints

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Process a query and return response with sources"""
    logger.info(f"📝 收到查询请求: {request.query[:100]}...")
    
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = rag_system.session_manager.create_session()
            logger.info(f"🆔 创建新会话: {session_id}")
        else:
            logger.info(f"🔄 使用现有会话: {session_id}")
        
        logger.info("🚀 开始处理查询...")
        
        # Process query using RAG system
        answer, sources = rag_system.query(request.query, session_id)
        
        logger.info(f"✅ 查询处理完成")
        logger.info(f"   答案长度: {len(answer)} 字符")
        logger.info(f"   来源数量: {len(sources)}")
        
        # Convert sources to proper format for frontend
        formatted_sources = []
        for source in sources:
            if isinstance(source, dict) and 'text' in source:
                # New format with link information - keep as dict for JSON serialization
                formatted_sources.append({
                    'text': source['text'],
                    'link': source.get('link')
                })
            else:
                # Legacy string format
                formatted_sources.append(str(source))
        
        return QueryResponse(
            answer=answer,
            sources=formatted_sources,
            session_id=session_id
        )
    except Exception as e:
        # 详细记录错误
        logger.error(f"❌ 查询处理失败: {str(e)}")
        logger.error(f"   异常类型: {type(e).__name__}")
        logger.error(f"   查询内容: {request.query}")
        logger.error(f"   完整堆栈:\n{traceback.format_exc()}")
        
        # 返回详细的错误信息
        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "query": request.query,
        }
        
        # 如果是认证相关错误，提供更多帮助信息
        if "unauthorized" in str(e).lower() or "401" in str(e):
            error_detail["help"] = "API 认证失败。请检查 OPENAI_API_KEY 配置。"
        elif "connection" in str(e).lower():
            error_detail["help"] = "网络连接失败。请检查 OPENAI_BASE_URL 配置和网络连接。"
        elif "timeout" in str(e).lower():
            error_detail["help"] = "请求超时。请检查网络连接或服务器状态。"
        
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/courses", response_model=CourseStats)
async def get_course_stats():
    """Get course analytics and statistics"""
    try:
        analytics = rag_system.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Load initial documents on startup"""
    docs_path = "../docs"
    if os.path.exists(docs_path):
        print("Loading initial documents...")
        try:
            courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")
        except Exception as e:
            print(f"Error loading documents: {e}")

# Custom static file handler with no-cache headers for development
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            # Add no-cache headers for development
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    
    
# Serve static files for the frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")