from dtos import SplitBillCreatedDTO
from repositories.transaction_repository import TransactionRepository
from repositories.account_repository import AccountRepository
from repositories.split_bill_repository import SplitBillRepository
from errors.custom_errors import (
    BadRequestError, 
    TransactionNotFoundError, 
    InvalidSplitAmountError, 
    InvalidAccountsError
)
from controllers.base_controller import BaseController

class SplitBillController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.trans_repo = TransactionRepository(self.context)
        self.acc_repo = AccountRepository(self.context)
        self.split_repo = SplitBillRepository(self.context)

    def create_split(self, transaction_key: str, payload: dict) -> SplitBillCreatedDTO:
        splits = payload["splits"]
        payers_keys = [split["account_key"] for split in splits]

        if len(payers_keys) != len(set(payers_keys)):
            raise BadRequestError("A lista de pagadores não pode conter contas duplicadas.")

        transaction = self.trans_repo.find_by_key(transaction_key)
        if not transaction:
            raise TransactionNotFoundError()

        total_split = sum(split["amount"] for split in splits)
        if total_split != transaction.amount:
            raise InvalidSplitAmountError(total_split, transaction.amount)

        accounts = self.acc_repo.find_many_by_keys(payers_keys)
        if len(accounts) != len(set(payers_keys)):
            raise InvalidAccountsError()

        account_map = {str(acc.account_key): acc.id for acc in accounts}
        
        splits_to_insert = [
            {"account_id": account_map[split["account_key"]], "amount": split["amount"]}
            for split in splits
        ]

        self.split_repo.create_splits(
            transaction_id=transaction.id,
            splits=splits_to_insert
        )

        self.session.commit()

        return SplitBillCreatedDTO()