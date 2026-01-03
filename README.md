# MarketPulse

A market data & signal detection platorm built with Python, FastAPI, Postgres, and Alembic.

## Current Status
### Market Data Ingestion
- Daily OHLCV price data sourced from **Stooq (public, free)**
- Supports multiple symbols (currently AAPL, MSFT, GOOGL, AMZN, NVDA)
- Append-only ingestion model (historical data is never rewritten)
- Safe to re-run at any time (idempotent)

### Database Design
- PostgreSQL with enforced uniqueness on `(symbol, date)`
- SQLAlchemy ORM models with Alembic migrations
- Local development via Docker

### Duplicate & Re-run Handling
- Ingestion checks the **latest date per symbol** and only inserts new rows
- Database-level uniqueness guarantees correctness
- Inserts are batched to avoid Postgres parameter limits
- Duplicate rows are safely ignored at the database layer

### Operational Safeguards
- Chunked inserts to respect Postgres parameter limits
- Explicit session lifecycle management
- Designed to run as a daily scheduled job


## Next Milestone
- Signal computation (e.g. rolling volatility, regime detection)
- FastAPI endpoints for computed signals
- Lightweight dashboard for inspection
- Macro data integration (FRED)
- Scheduled execution (cron / task runner)