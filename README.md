# MarketPulse

MarketPulse is a market data ingestion and signal platform built to model how real-world financial data systems are designed: incremental, idempotent, and interpretation-driven.

The project focuses on **data correctness, volatility regime detection, and operational realism**, rather than prediction or trading execution.

---

## Current Capabilities

### Market Data Ingestion
- Daily OHLCV price data sourced from **Stooq (public, free)**
- Supports multiple symbols (AAPL, MSFT, GOOGL, AMZN, NVDA)
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

---

## Signal Engine

### Implemented Signals
- **20-day realized volatility (annualized)**
- **1-year volatility percentile**
- Volatility regime classification via interpretable flags

### Volatility Regime Flags
- `VOL_SPIKE` — volatility at extreme highs relative to recent history
- `VOL_ELEVATED` — meaningfully above-normal volatility
- `VOL_CRUSH` — historically low volatility regime
- `ABS_HIGH_VOL` / `ABS_LOW_VOL` — absolute cross-asset sanity checks

Signals are **regime-aware**, asset-relative, and designed to be interpreted probabilistically rather than as price predictions.

---

## API

Signals are exposed via FastAPI endpoints:

- `GET /signals/volatility/{symbol}`
- `GET /signals/today`

Each response includes:
- symbol
- lookback window
- realized volatility
- volatility percentile
- regime flags

---

## Design Philosophy
- Append-only data pipelines
- Idempotent jobs and safe re-runs
- Database-enforced correctness over application logic
- Signals provide **context**, not predictions
- Operational constraints treated as first-class concerns

---

## Next Milestones
- Volatility regime transitions (compression → expansion)
- Risk state aggregation (RISK_ON / NEUTRAL / RISK_OFF)
- Macro data integration (FRED)
- Scheduled execution (cron / task runner)
- Lightweight inspection dashboard