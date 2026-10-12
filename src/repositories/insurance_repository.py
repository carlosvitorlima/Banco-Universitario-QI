import uuid
from sqlalchemy.exc import IntegrityError
from database import Context
from models.insurance import Insurance, ContractedInsurance
from errors.custom_errors import InsuranceAlreadyContractedError

class InsuranceRepository:
    def __init__(self, context: Context):
        self.session = context.db_session

    def find_insurance(self, insurance_id: int) -> Insurance:
        return self.session.query(Insurance).filter_by(id=insurance_id).first()

    def contract(self, customer_id: int, insurance_id: int) -> ContractedInsurance:
        try:
            contract = ContractedInsurance(
                policy_number=str(uuid.uuid4()), 
                customer_id=customer_id,
                insurance_id=insurance_id
            )
            self.session.add(contract)
            self.session.flush() 
            return contract
            
        except IntegrityError:
            raise InsuranceAlreadyContractedError()