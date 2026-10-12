from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_key = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    
    idempotency_key = Column(String(100), unique=True, nullable=False)
    
    origin_account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    destination_account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)