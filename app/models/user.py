import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null for pure OAuth users
    avatar_url = Column(String(500), nullable=True)
    auth_provider = Column(String(50), default="email")  # "email" or "google"
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def verify_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()
