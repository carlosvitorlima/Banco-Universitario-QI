from repositories.customer_repository import CustomerRepository
from connectors.university_connector import UniversityConnector
from requests.exceptions import Timeout
from dtos import CustomerCreatedDTO
from utils.document_number import is_valid_cpf
from errors.custom_errors import (
    InvalidDocumentError,
    InvalidAcademicBondError,
    UniversityApiError,
    UniversityApiTimeoutError,
)
from controllers.base_controller import BaseController

class CustomerController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.repository = CustomerRepository(self.context)
        self.connector = UniversityConnector()

    def create_customer(self, payload: dict) -> CustomerCreatedDTO:
        document = payload["document"]
        university_id = payload["university_id"]
        course_id = payload["course_id"]

        if not is_valid_cpf(document):
            raise InvalidDocumentError(document)

        try:
            enrollment_response = self.connector.check_student_enrollment(document, university_id)
        except Timeout:
            raise UniversityApiTimeoutError() from None

        if enrollment_response.status == 404:
            raise InvalidAcademicBondError()
        if enrollment_response.status != 200:
            raise UniversityApiError()

        customer = self.repository.create(
            document=document,
            university_id=university_id,
            course_id=course_id
        )

        self.session.commit()

        return CustomerCreatedDTO.from_model(customer)