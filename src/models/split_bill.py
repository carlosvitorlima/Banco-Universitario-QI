from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from models.base import Base

class SplitBill(Base):
    __tablename__ = 'split_bill'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('transaction.id'), nullable=False)
    payer_account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    
    amount = Column(BigInteger, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)