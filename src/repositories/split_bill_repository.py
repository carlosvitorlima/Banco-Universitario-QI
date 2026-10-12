from database import Context
from models.split_bill import SplitBill

class SplitBillRepository:
    def __init__(self, context: Context):
        self.session = context.db_session

    def create_splits(self, transaction_id: int, splits: list[dict]):
        split_records = [
            SplitBill(
                transaction_id=transaction_id,
                payer_account_id=split["account_id"],
                amount=split["amount"]
            )
            for split in splits
        ]
        
        self.session.add_all(split_records)
        self.session.flush()