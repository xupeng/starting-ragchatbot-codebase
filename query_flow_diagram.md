# RAG系统查询流程图

```mermaid
graph TD
    A[用户输入查询] --> B[前端JavaScript sendMessage]
    B --> C[禁用输入框 显示加载状态]
    C --> D[发送POST请求 /api/query]
    
    D --> E[FastAPI路由 query_documents]
    E --> F{会话ID存在?}
    F -->|否| G[创建新会话]
    F -->|是| H[使用现有会话]
    G --> I[RAG系统处理 rag_system.query]
    H --> I
    
    I --> J[构建提示词 获取对话历史]
    J --> K[调用AI生成器 generate_response]
    
    K --> L[Claude API调用 系统提示+工具定义]
    L --> M{Claude决策: 需要搜索?}
    
    M -->|是| N[调用搜索工具 search_course_content]
    N --> O[向量存储查询 vector_store.search]
    O --> P[ChromaDB语义搜索 sentence-transformers]
    P --> Q[返回相关文档块]
    Q --> R[Claude基于搜索结果 生成答案]
    
    M -->|否| S[Claude使用 已有知识回答]
    
    R --> T[更新会话历史 session_manager]
    S --> T
    T --> U[返回JSON响应 answer,sources,session_id]
    
    U --> V[前端接收响应 script.js]
    V --> W[移除加载状态]
    W --> X[显示AI回答]
    X --> Y[显示来源信息 可折叠]
    Y --> Z[重新启用输入框]
    
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef ai fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storage fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef decision fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    
    class A,B,C,D,V,W,X,Y,Z frontend
    class E,F,G,H,I,J,U,T backend
    class K,L,M,R,S ai
    class N,O,P,Q storage
    class M decision
```

## 主要组件说明

### 🖥️ 前端层 (Frontend)
- **用户界面**: HTML/CSS/JavaScript
- **状态管理**: 会话ID、加载状态、消息历史
- **HTTP通信**: Fetch API与后端交互

### 🔧 FastAPI层 (API Layer)  
- **路由处理**: `/api/query` 端点
- **请求验证**: Pydantic模型验证
- **会话管理**: 创建/维护用户会话

### 🧠 RAG系统核心 (RAG Core)
- **查询编排**: 协调各个组件
- **上下文管理**: 对话历史和会话状态
- **AI集成**: Claude API调用

### 🤖 AI处理层 (AI Layer)
- **智能决策**: 判断是否需要搜索
- **工具使用**: 调用搜索工具获取信息
- **答案合成**: 基于搜索结果生成回答

### 🗄️ 数据存储层 (Storage Layer)
- **向量数据库**: ChromaDB存储文档嵌入
- **语义搜索**: sentence-transformers模型
- **文档检索**: 相关内容块匹配

## 数据流

1. **用户查询** → HTTP POST请求
2. **API验证** → 会话管理
3. **RAG处理** → AI生成器调用  
4. **Claude决策** → 工具使用/直接回答
5. **搜索执行** → 向量相似度匹配
6. **答案生成** → 上下文增强响应
7. **前端展示** → 用户界面更新