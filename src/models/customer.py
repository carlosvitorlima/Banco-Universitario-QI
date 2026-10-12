import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base

class University(Base):
    __tablename__ = 'university'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class Course(Base):
    __tablename__ = 'course'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class Customer(Base):
    __tablename__ = 'customer'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_key = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    document = Column(String(11), unique=True, nullable=False) 
    
    university_id = Column(Integer, ForeignKey('university.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    university = relationship("University")
    course = relationship("Course")