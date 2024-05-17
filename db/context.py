from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Asset(Base):
    __tablename__ = "asset"
    ticker: Mapped[str] = mapped_column(String(), primary_key=True)
    def __repr__(self) -> str:
        return f"Asset(ticker={self.ticker!r})"
    
class AssetDailyPrice(Base):
    __tablename__ = "asset_daily_price"
    ticker: Mapped[str] = mapped_column(String(), primary_key=True)
    date: Mapped[str] = mapped_column(String(), primary_key=True)
    adj_close: Mapped[float]
    def __repr__(self) -> str:
        return f"Asset daily price(ticker={self.ticker!r}, date={self.date!r}, close={self.adj_close!r})"
    
class AssetDividends(Base):
    __tablename__ = "asset_dividends"
    ticker: Mapped[str] = mapped_column(String(), primary_key=True)
    date: Mapped[str] = mapped_column(String(), primary_key=True)
    dividend_per_share: Mapped[float]
    def __repr__(self) -> str:
        return f"Asset dividend(ticker={self.ticker!r}, date={self.date!r}, dividend={self.dividend_per_share!r})"