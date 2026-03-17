# Swift Dependency Graph Service

Production-ready Graph Layer for the Swift Event Intelligence Platform. Real-time world model of dependencies across infrastructure, economies, organizations, and geography.

## Features

- **Neo4j** graph database with constraints and indexes
- **FastAPI** microservice with async processing
- **Core queries**: dependencies, impact propagation, shortest path, weighted paths, subgraph extraction
- **Redis** caching for frequent queries
- **Kafka** streaming ingestion for real-time updates
- **Batch ingestion** from OSM, World Bank, trade datasets
- **Security**: API key auth, rate limiting, input validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment (copy .env.example to .env)
cp .env.example .env

# Run Neo4j and Redis (Docker)
docker-compose up -d neo4j redis

# Initialize schema and run batch ingest
python -m scripts.batch_ingest

# Start API
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /nodes/ | Create/update node |
| GET | /nodes/{id} | Get node by id |
| POST | /edges/ | Create/update edge |
| GET | /dependencies/{id} | Multi-hop dependencies |
| GET | /impact-paths/{id} | Impact propagation |
| GET | /shortest-path?from_id=&to_id= | Shortest path |
| GET | /weighted-paths/{id} | Weighted propagation paths |
| POST | /subgraph/query | Subgraph by region/industry |

## Kafka Message Format

```json
{
  "action": "ADD_EDGE",
  "from": "infra:airport_ist",
  "to": "ind:tourism_tr",
  "type": "SERVES",
  "weight": 0.9,
  "confidence": 0.95
}
```

## Node Types

Location, Infrastructure, Industry, Organization, SupplyChain

## Relationship Types

LOCATED_IN, PHYSICALLY_CONNECTED_TO, LOGISTICALLY_DEPENDS_ON, ECONOMICALLY_DEPENDS_ON, SUPPLIES, SERVES, OWNED_BY, ROUTES_THROUGH
