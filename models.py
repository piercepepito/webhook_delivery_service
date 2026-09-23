from sqlalchemy import String, Boolean, DateTime, Uuid, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import text

from datetime import datetime

from db import Base

class Subscriptions(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    event_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

class Events(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class Deliveries(Base):
    __tablename__="deliveries"
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    event_id: Mapped[str] = mapped_column(Uuid, ForeignKey("events.id"), nullable=False)
    subscription_id: Mapped[str] = mapped_column(Uuid, ForeignKey("subscriptions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("pending"))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1')
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))

class DeliveryAttempts(Base):
    __tablename__="delivery_attempts"
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    delivery_id: Mapped[str] = mapped_column(Uuid, ForeignKey("deliveries.id"), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer)
    response_snippet: Mapped[str] = mapped_column(String)
    error: Mapped[str] = mapped_column(String)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))
