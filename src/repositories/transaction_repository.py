import uuid
from sqlalchemy.exc import IntegrityError
from database import Context
from models.transaction import Transaction
from errors.custom_errors import TransactionConflictError

class TransactionRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def find_by_key(self, transaction_key: str) -> Transaction:
        return self.session.query(Transaction).filter_by(transaction_key=transaction_key).first()

    def create(self, transaction: Transaction):
        transaction.transaction_key = uuid.uuid4()

        try:
            self.session.add(transaction)
            self.session.flush() 
            return transaction
            
        except IntegrityError:
            raise TransactionConflictError()
        
    def get_account_transactions(self, account_id: int, limit: int, cursor_id: int = None) -> list[Transaction]:
        query = self.session.query(Transaction).filter(
            (Transaction.origin_account_id == account_id) | 
            (Transaction.destination_account_id == account_id)
        )
        if cursor_id:
            query = query.filter(Transaction.id > cursor_id)
            
        return query.order_by(Transaction.id.asc()).limit(limit).all()