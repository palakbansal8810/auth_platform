from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Table
from datetime import datetime
from app.database import Base
import enum
from sqlalchemy.orm import relationship

class ProviderType(str, enum.Enum):
    local = "local"
    google = "google"
    okta = "okta"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    providers = relationship("AuthProvider", back_populates="user")


class AuthProvider(Base):
    __tablename__ = "auth_providers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String)  # "local", "google", "okta"
    provider_user_id = Column(String)
    password_hash = Column(String, nullable=True)

    user = relationship("User", back_populates="providers")