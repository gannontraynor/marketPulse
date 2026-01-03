from sqlalchemy import Column, Integer, String, Date, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class DailyBar(Base):
    __tablename__ = "daily_bars"
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uniq_symbol_date'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)