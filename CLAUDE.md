# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application

```bash
# Quick start with shell script
chmod +x run.sh
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Environment Setup

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env to add ANTHROPIC_API_KEY
```

### Access Points

- Web Interface: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>
- API Base URL: <http://localhost:8000/api>

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) system** for course materials with a tool-enhanced Claude AI architecture.

### Core Components

**RAG System Flow** (`backend/rag_system.py`):

- Main orchestrator that coordinates document processing, vector search, AI generation, and session management
- Uses tool-enhanced approach where Claude decides whether to search or answer directly
- Integrates with ChromaDB for vector storage and Anthropic Claude for AI responses

**Document Processing Pipeline**:

1. `document_processor.py`: Parses structured course files (title/instructor/lessons), chunks content with sentence-aware splitting and overlap
2. `vector_store.py`: ChromaDB integration with sentence-transformers embeddings (`all-MiniLM-L6-v2`)
3. Content indexed as `CourseChunk` objects with course/lesson metadata for precise retrieval

**AI Tool Integration** (`ai_generator.py` + `search_tools.py`):

- Claude uses `search_course_content` tool for semantic search when needed
- System prompt guides Claude to decide between direct answers vs. tool-assisted responses
- Tool manager handles search execution and result formatting

**Session Management** (`session_manager.py`):

- Maintains conversation history (configurable `MAX_HISTORY=2`)
- Enables multi-turn dialogue context

### Data Models (`models.py`)

- `Course`: Course metadata (title, instructor, link)
- `Lesson`: Individual lesson within course (number, title, link)
- `CourseChunk`: Searchable content blocks with course/lesson context

### Configuration (`config.py`)

Key settings:

- `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100` for document processing
- `MAX_RESULTS=5` for search results
- `ANTHROPIC_MODEL="claude-sonnet-4-20250514"`
- `CHROMA_PATH="./chroma_db"` for vector storage

### File Structure

```
backend/           # Python FastAPI backend
  app.py          # FastAPI routes and CORS setup
  rag_system.py   # Main RAG orchestrator
  ai_generator.py # Claude API integration with tools
  search_tools.py # Tool definitions and execution
  vector_store.py # ChromaDB vector database
  document_processor.py # Document parsing and chunking
  session_manager.py    # Conversation state
  models.py       # Data models
  config.py       # Configuration management

frontend/         # Pure HTML/CSS/JS interface
docs/            # Course material files (.txt format)
```

### Document Format

Course files follow this structure:

```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 0: [title]
Lesson Link: [url]
[lesson content...]
```

### API Endpoints

- `POST /api/query`: Main query endpoint (query, session_id → answer, sources, session_id)
- `GET /api/courses`: Course statistics (total_courses, course_titles)

## Technical Notes

- Uses `uv` for Python package management and execution
- FastAPI with auto-reload for development
- ChromaDB persists in `./chroma_db` directory
- Frontend served as static files from `/frontend`
- Documents auto-loaded from `../docs` on startup
- Session-based conversation history with configurable limits
- Claude intelligently chooses between direct answers and tool-assisted search
- the server is running, no need to start it.