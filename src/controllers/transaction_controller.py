from dtos import TransactionCreatedDTO, TransactionStatementDTO
from models.transaction import Transaction
from repositories.transaction_repository import TransactionRepository
from repositories.account_repository import AccountRepository
from errors.custom_errors import (
    AccountNotFoundError,
    InsufficientBalanceError,
    SameAccountTransferError,
)
from controllers.base_controller import BaseController

class TransactionController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.trans_repo = TransactionRepository(self.context)
        self.acc_repo = AccountRepository(self.context)

    def execute_transfer(self, payload: dict) -> TransactionCreatedDTO:
        idempotency_key = payload["idempotency_key"]
        origin_key = payload["origin_account_key"]
        dest_key = payload["destination_account_key"]
        amount = payload["amount"]

        if origin_key == dest_key:
            raise SameAccountTransferError()

        accounts = self.acc_repo.get_accounts_for_update_by_keys([origin_key, dest_key])

        origin_account = next((acc for acc in accounts if str(acc.account_key) == origin_key), None)
        destination_account = next((acc for acc in accounts if str(acc.account_key) == dest_key), None)

        if not origin_account or not destination_account:
            raise AccountNotFoundError()

        if origin_account.balance < amount:
            raise InsufficientBalanceError()

        origin_account.balance -= amount
        destination_account.balance += amount

        transaction = Transaction(
            origin_account_id=origin_account.id,
            destination_account_id=destination_account.id,
            amount=amount,
            idempotency_key=idempotency_key
        )
        self.trans_repo.create(transaction)

        self.session.commit()
        
        return TransactionCreatedDTO.from_model(transaction)
    
    def get_statement(
        self,
        account_key: str,
        limit: int,
        cursor: int = None,
    ) -> TransactionStatementDTO:
        account_info = self.acc_repo.find_by_key(account_key)
        if not account_info:
            raise AccountNotFoundError()

        transactions = self.trans_repo.get_account_transactions(
            account_id=account_info.id,
            limit=limit,
            cursor_id=cursor
        )

        return TransactionStatementDTO.from_models(account_info.id, transactions)