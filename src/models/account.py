import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base

class AccountStatus(Base):
    __tablename__ = 'account_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

class AccountType(Base):
    __tablename__ = 'account_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

class Account(Base):
    __tablename__ = 'account'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_key = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    status_id = Column(Integer, ForeignKey('account_status.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('account_type.id'), nullable=False)
    
    balance = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        CheckConstraint('balance >= 0', name='check_balance_positive'),
    )

class AccountStatusEvent(Base):
    __tablename__ = 'account_status_event'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    from_status_id = Column(Integer, ForeignKey('account_status.id'), nullable=True)
    to_status_id = Column(Integer, ForeignKey('account_status.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)