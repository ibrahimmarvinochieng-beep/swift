# Swift Personal Context Engine

Real-time personalization layer that maps global event intelligence to individual users.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8002
```

## API

- **POST /users/** - Create user
- **GET /users/{user_id}** - Get user
- **PATCH /users/{user_id}** - Update user
- **GET /feed/{user_id}** - Personalized feed
- **POST /interactions/** - Record click/view/save

## Config

| Env | Default |
|-----|---------|
| CONTEXT_DATABASE_URL | sqlite+aiosqlite:///./context.db |
| CONTEXT_REDIS_URL | redis://localhost:6379/2 |
| CONTEXT_IMPACT_ENGINE_URL | http://localhost:8001 |
