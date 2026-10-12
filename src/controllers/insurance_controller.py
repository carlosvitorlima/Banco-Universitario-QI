from dtos import InsuranceContractedDTO
from repositories.insurance_repository import InsuranceRepository
from repositories.customer_repository import CustomerRepository
from errors.custom_errors import CustomerNotFoundError, InsuranceNotFoundError
from controllers.base_controller import BaseController

class InsuranceController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.ins_repo = InsuranceRepository(self.context)
        self.cust_repo = CustomerRepository(self.context)

    def contract_insurance(self, payload: dict) -> InsuranceContractedDTO:
        customer_key = payload["customer_key"]
        insurance_id = payload["insurance_id"]

        customer = self.cust_repo.find_by_key(customer_key)
        if not customer:
            raise CustomerNotFoundError()

        insurance = self.ins_repo.find_insurance(insurance_id)
        if not insurance:
            raise InsuranceNotFoundError()

        contract = self.ins_repo.contract(
            customer_id=customer.id,
            insurance_id=insurance.id
        )

        self.session.commit()

        return InsuranceContractedDTO.from_model(contract)