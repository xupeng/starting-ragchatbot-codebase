import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class ConfigError(Exception):
    """Configuration related errors"""
    pass

@dataclass
class Config:
    """Configuration settings for the RAG system"""
    # Gemini API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    def validate(self) -> None:
        """验证配置是否有效"""
        errors = []
        
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY 是必需的，请在 .env 文件中设置")
        
        
        if not self.GEMINI_MODEL:
            errors.append("GEMINI_MODEL 不能为空")
        
        if errors:
            raise ConfigError(f"配置验证失败:\n" + "\n".join(f"- {error}" for error in errors))
    
    def print_config(self, hide_sensitive: bool = True) -> None:
        """打印配置信息用于调试"""
        print("=== RAG 系统配置 ===")
        
        # API Key 显示（隐藏敏感信息）
        api_key_display = ""
        if self.GEMINI_API_KEY:
            if hide_sensitive:
                api_key_display = f"{self.GEMINI_API_KEY[:8]}..." if len(self.GEMINI_API_KEY) > 8 else "****"
            else:
                api_key_display = self.GEMINI_API_KEY
        else:
            api_key_display = "未设置"
        
        print(f"Gemini API Key: {api_key_display}")
        print(f"Gemini Model: {self.GEMINI_MODEL}")
        print(f"Embedding Model: {self.EMBEDDING_MODEL}")
        print(f"Chunk Size: {self.CHUNK_SIZE}")
        print(f"Max Results: {self.MAX_RESULTS}")
        print("=" * 25)
    
    # Embedding model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Document processing settings
    CHUNK_SIZE: int = 800       # Size of text chunks for vector storage
    CHUNK_OVERLAP: int = 100     # Characters to overlap between chunks
    MAX_RESULTS: int = 5         # Maximum search results to return
    MAX_HISTORY: int = 2         # Number of conversation messages to remember
    
    # Database paths
    CHROMA_PATH: str = "./chroma_db"  # ChromaDB storage location

config = Config()

# 在模块加载时验证配置
try:
    config.validate()
except ConfigError as e:
    print(f"⚠️ 配置错误: {e}")
    print("\n请检查你的 .env 文件并确保所有必需的环境变量都已设置。")
    print("可以运行 'python check_config.py' 来获取详细的配置检查。")


