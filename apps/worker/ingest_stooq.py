import csv
import datetime as dt
import urllib.request

from typing import Optional, Tuple, List, TypeVar

T = TypeVar("T")

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from packages.core.db import SessionLocal
from packages.core.models import DailyBar

STOOQ_DAILY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"

def chunked(items: List[T], size: int) -> List[List[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]

def fetch_daily_csv(symbol: str) -> list[dict]:
    url = STOOQ_DAILY_URL.format(symbol=symbol.lower())
    with urllib.request.urlopen(url) as resp:
        raw = resp.read().decode("utf-8")

    reader = csv.DictReader(raw.splitlines())
    rows = list(reader)
    if not rows:
        raise RuntimeError(f"No data returned for {symbol} from {url}")
    return rows


def upsert_daily_bars(symbol: str, rows: list[dict]) -> int:
    session = SessionLocal()
    try:
        latest = get_latest_date(symbol, session)

        payload = []
        for r in rows:
            bar_date = dt.date.fromisoformat(r["Date"])

            # append-only: skip anything already ingested
            if latest and bar_date <= latest:
                continue

            payload.append(
                {
                    "symbol": symbol.upper(),
                    "date": bar_date,
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                    "volume": float(r["Volume"]) if r.get("Volume") else 0.0,
                }
            )

        if not payload:
            return 0

        inserted = 0
        for batch in chunked(payload, 3000):
            session.execute(insert(DailyBar).values(batch))
            inserted += len(batch)

        session.commit()
        return inserted
    finally:
        session.close()


def get_latest_date(symbol: str, session) -> Optional[dt.date]:
    q = select(func.max(DailyBar.date)).where(DailyBar.symbol == symbol.upper())
    return session.execute(q).scalar()

def verify(symbol: str) -> Tuple[int, Optional[dt.date], Optional[dt.date]]:
    session = SessionLocal()
    try:
        q = select(DailyBar.date).where(DailyBar.symbol == symbol.upper()).order_by(DailyBar.date.asc())
        dates = [row[0] for row in session.execute(q).all()]
        if not dates:
            return 0, None, None
        return len(dates), dates[0], dates[-1]
    finally:
        session.close()


if __name__ == "__main__":
    symbols = ["aapl.us", "msft.us", "googl.us", "amzn.us", "nvda.us", "spy.us"]

    for symbol in symbols:
        print(f"\nProcessing {symbol}...")
        rows = fetch_daily_csv(symbol)
        inserted = upsert_daily_bars(symbol, rows)

        n, first_d, last_d = verify(symbol)
        print(f"Inserted {inserted} new rows; DB now has {n} rows for {symbol.upper()} ({first_d} → {last_d})")