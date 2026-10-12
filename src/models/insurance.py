import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base

class Insurance(Base):
    __tablename__ = 'insurance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    monthly_premium = Column(Integer, nullable=False)

class ContractedInsurance(Base):
    __tablename__ = 'contracted_insurance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    insurance_id = Column(Integer, ForeignKey('insurance.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    
    policy_number = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        UniqueConstraint('insurance_id', 'customer_id', name='unique_customer_insurance'),
    )