import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base

class Partner(Base):
    __tablename__ = 'partner'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

class Benefit(Base):
    __tablename__ = 'benefit'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    benefit_key = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    partner_id = Column(Integer, ForeignKey('partner.id'), nullable=False)
    
    title = Column(String(150), nullable=False)
    
    target_university_id = Column(Integer, ForeignKey('university.id'), nullable=True)
    target_course_id = Column(Integer, ForeignKey('course.id'), nullable=True)

class BenefitRedemption(Base):
    __tablename__ = 'benefit_redemption'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    benefit_id = Column(Integer, ForeignKey('benefit.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    
    voucher_code = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('benefit_id', 'customer_id', name='unique_customer_benefit_redemption'),
    )