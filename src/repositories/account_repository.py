from database import Context
from models.account import Account, AccountStatus, AccountStatusEvent

class AccountRepository:
    def __init__(self, context: Context):
        self.session = context.db_session

    def find_by_key(self, account_key: str) -> Account:
        return self.session.query(Account).filter_by(account_key=account_key).first()

    def find_many_by_keys(self, account_keys: list[str]) -> list[Account]:
        return self.session.query(Account).filter(Account.account_key.in_(account_keys)).all()

    def get_account_for_update_by_key(self, account_key: str) -> Account:
        return self.session.query(Account).filter_by(account_key=account_key).with_for_update().first()

    def get_status_by_name(self, name: str) -> AccountStatus:
        return self.session.query(AccountStatus).filter_by(name=name).first()

    def create_with_event(self, customer_id: int, type_id: int, status_id: int) -> Account:
        new_account = Account(
            customer_id=customer_id,
            type_id=type_id,
            status_id=status_id
        )
        self.session.add(new_account)
        self.session.flush()
        
        initial_event = AccountStatusEvent(
            account_id=new_account.id,
            from_status_id=None, 
            to_status_id=status_id
        )
        self.session.add(initial_event)
        self.session.flush()
        
        return new_account
    
    def get_accounts_for_update_by_keys(self, account_keys: list[str]) -> list[Account]:
        return (
            self.session.query(Account)
            .filter(Account.account_key.in_(account_keys))
            .with_for_update()
            .order_by(Account.id.asc())
            .all()
        )