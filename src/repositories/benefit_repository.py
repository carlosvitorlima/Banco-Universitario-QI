import uuid
from sqlalchemy.exc import IntegrityError
from database import Context
from models.benefit import Benefit, BenefitRedemption, Partner
from errors.custom_errors import BenefitAlreadyRedeemedError

class BenefitRepository:
    def __init__(self, context: Context):
        self.session = context.db_session

    def find_by_key(self, benefit_key: str) -> Benefit:
        return self.session.query(Benefit).filter_by(benefit_key=benefit_key).first()

    def find_all_paginated(self, limit: int, cursor_id: int = None) -> list[tuple[Benefit, Partner]]:
        query = (
            self.session.query(Benefit, Partner)
            .join(Partner, Benefit.partner_id == Partner.id)
        )
        
        if cursor_id:
            query = query.filter(Benefit.id > cursor_id)
            
        return query.order_by(Benefit.id.asc()).limit(limit + 1).all()

    def create_redemption(self, benefit_id: int, customer_id: int) -> BenefitRedemption:
        try:
            voucher = f"QI-{str(uuid.uuid4())[:8].upper()}"
            
            redemption = BenefitRedemption(
                benefit_id=benefit_id,
                customer_id=customer_id,
                voucher_code=voucher
            )
            self.session.add(redemption)
            self.session.flush()
            
            return redemption
            
        except IntegrityError:
            raise BenefitAlreadyRedeemedError()