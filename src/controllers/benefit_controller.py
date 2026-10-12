from dtos import BenefitListDTO, BenefitRedemptionDTO
from repositories.benefit_repository import BenefitRepository
from repositories.customer_repository import CustomerRepository
from errors.custom_errors import (
    CustomerNotFoundError, 
    BenefitNotFoundError, 
    IneligibleUniversityError, 
    IneligibleCourseError
)
from controllers.base_controller import BaseController

class BenefitController(BaseController):
    def __init__(self, class_name: str):
        super().__init__(class_name)
        self.benefit_repo = BenefitRepository(self.context)
        self.customer_repo = CustomerRepository(self.context)

    def list_benefits(self, limit: int, cursor: int = None) -> BenefitListDTO:
        results = self.benefit_repo.find_all_paginated(limit, cursor)
        
        has_next = len(results) > limit
        benefits_to_return = results[:limit]
        
        next_cursor = benefits_to_return[-1][0].id if has_next else None
        
        return BenefitListDTO.from_models(
            benefits=benefits_to_return,
            next_cursor=next_cursor
        )
        
    def redeem_benefit(self, benefit_key: str, payload: dict) -> BenefitRedemptionDTO:
        customer_key = payload["customer_key"]

        customer = self.customer_repo.find_by_key(customer_key)
        if not customer:
            raise CustomerNotFoundError()

        benefit = self.benefit_repo.find_by_key(benefit_key)
        if not benefit:
            raise BenefitNotFoundError()

        if benefit.target_university_id and benefit.target_university_id != customer.university_id:
            raise IneligibleUniversityError()

        if benefit.target_course_id and benefit.target_course_id != customer.course_id:
            raise IneligibleCourseError()

        redemption = self.benefit_repo.create_redemption(
            benefit_id=benefit.id,
            customer_id=customer.id
        )

        self.session.commit()

        return BenefitRedemptionDTO.from_model(redemption)