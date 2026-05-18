# Sahel Dev - Database Models
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PlanEnum(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    plan = Column(Enum(PlanEnum), default=PlanEnum.FREE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    monitors = relationship("Monitor", back_populates="owner")
    status_pages = relationship("StatusPage", back_populates="owner")


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    method = Column(String, default="GET")
    interval = Column(Integer, default=300)  # seconds
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="monitors")
    checks = relationship("Check", back_populates="monitor")
    incidents = relationship("Incident", back_populates="monitor")


class StatusPage(Base):
    __tablename__ = "status_pages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, default="")
    is_public = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="status_pages")
    monitors = relationship("StatusPageMonitor", back_populates="status_page")


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # ms
    is_up = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    monitor = relationship("Monitor", back_populates="checks")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    status = Column(String, default="detected")  # detected, resolved
    started_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    monitor = relationship("Monitor", back_populates="incidents")


class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    channel_type = Column(String, nullable=False)  # email, slack, discord, sms
    config = Column(String, nullable=False)  # JSON webhook URL or email
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StatusPageMonitor(Base):
    __tablename__ = "status_page_monitors"

    id = Column(Integer, primary_key=True, index=True)
    status_page_id = Column(Integer, ForeignKey("status_pages.id"), nullable=False)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
Base.metadata.create_all(bind=engine)