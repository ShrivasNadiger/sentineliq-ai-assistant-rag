# SentinelIQ AI Assistant (RAG)

# Tool-75 — AI Service

Flask-based AI microservice for Tool-75: AI Assistant with RAG.

## Tech Stack

- Python 3.11 + Flask 3.x
- Groq API (LLaMA-3.3-70b-versatile)
- ChromaDB (vector database)
- Redis (response caching)

## Prerequisites

- Python 3.11+
- Docker (for Redis)
- Groq API key from console.groq.com

## Setup

```bash
# 1. Clone and enter directory
cd ai-service

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Start Redis
docker run -d -p 6379:6379 --name redis-tool75 redis:7

# 6. Seed ChromaDB
python chroma_seeder.py

# 7. Start the service
python app.py
```

## Endpoints

| Method | Endpoint              | Description                  |
| ------ | --------------------- | ---------------------------- |
| GET    | /health               | Service health status        |
| POST   | /describe             | Generate AI description      |
| POST   | /recommend            | Get AI recommendations       |
| POST   | /categorise           | Classify input into category |
| POST   | /generate-report      | Submit async report job      |
| GET    | /generate-report/<id> | Poll report job status       |
| POST   | /query                | RAG pipeline query           |
| POST   | /analyse-document     | Analyse document content     |

## Environment Variables

| Variable           | Description                          |
| ------------------ | ------------------------------------ |
| GROQ_API_KEY       | Groq API key from console.groq.com   |
| FLASK_PORT         | Port to run Flask on (default: 5000) |
| REDIS_URL          | Redis connection URL                 |
| CHROMA_PERSIST_DIR | ChromaDB storage directory           |

## Health Check

```
GET http://localhost:5000/health
```
