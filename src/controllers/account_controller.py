from dtos import AccountCreatedDTO
from repositories.account_repository import AccountRepository
from repositories.customer_repository import CustomerRepository
from errors.custom_errors import CustomerNotFoundError, StatusNotConfiguredError
from controllers.base_controller import BaseController

class AccountController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.account_repo = AccountRepository(self.context)
        self.customer_repo = CustomerRepository(self.context)

    def create_account(self, payload: dict) -> AccountCreatedDTO:
        customer_key = payload["customer_key"]
        type_id = payload["type_id"]

        customer = self.customer_repo.find_by_key(customer_key)
        if not customer:
            raise CustomerNotFoundError()

        initial_status = self.account_repo.get_status_by_name("ACTIVE")
        if not initial_status:
            raise StatusNotConfiguredError()

        account = self.account_repo.create_with_event(
            customer_id=customer.id,
            type_id=type_id,
            status_id=initial_status.id
        )

        self.session.commit()

        return AccountCreatedDTO.from_model(account)