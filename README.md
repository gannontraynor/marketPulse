# MarketPulse

A market data & signal detection platorm built with Python, FastAPI, Postgres, and Alembic.

## Current Status
- Repo scaffold (appps/api, apps/worker, packages/core)
- Postgres running via Docker
- SQLAlchemy models & Alembic migrations wired

## Next Milestone
- Innjest first 5 tickers of daily OHLCV data (Open, High, Low, Close, Volume)
- Copute first signal (20D volatility) expose via API