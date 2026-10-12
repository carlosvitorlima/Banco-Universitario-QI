from sqlalchemy.exc import IntegrityError
from database import Context
from models.customer import Customer
from errors.custom_errors import DuplicatedCustomerError

class CustomerRepository:
    def __init__(self, context: Context):
        self.session = context.db_session

    def find_by_key(self, customer_key: str) -> Customer:
        return self.session.query(Customer).filter_by(customer_key=customer_key).first()

    def create(self, document: str, university_id: int, course_id: int) -> Customer:
        try:
            new_customer = Customer(
                document=document,
                university_id=university_id,
                course_id=course_id
            )
            self.session.add(new_customer)
            self.session.flush() 
            
            return new_customer
            
        except IntegrityError:
            raise DuplicatedCustomerError()