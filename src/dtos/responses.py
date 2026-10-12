from dataclasses import dataclass

from models.account import Account
from models.benefit import Benefit, BenefitRedemption, Partner
from models.customer import Customer
from models.insurance import ContractedInsurance
from models.transaction import Transaction


@dataclass(frozen=True)
class AccountCreatedDTO:
    account_key: str

    @classmethod
    def from_model(cls, account: Account) -> "AccountCreatedDTO":
        return cls(account_key=str(account.account_key))


@dataclass(frozen=True)
class CustomerCreatedDTO:
    customer_key: str

    @classmethod
    def from_model(cls, customer: Customer) -> "CustomerCreatedDTO":
        return cls(customer_key=str(customer.customer_key))


@dataclass(frozen=True)
class BenefitRedemptionDTO:
    voucher_code: str

    @classmethod
    def from_model(cls, redemption: BenefitRedemption) -> "BenefitRedemptionDTO":
        return cls(voucher_code=redemption.voucher_code)


@dataclass(frozen=True)
class PartnerDTO:
    id: int
    name: str


@dataclass(frozen=True)
class BenefitDTO:
    benefit_key: str
    title: str
    partner: PartnerDTO
    target_university_id: int | None
    target_course_id: int | None

    @classmethod
    def from_models(cls, benefit: Benefit, partner: Partner) -> "BenefitDTO":
        return cls(
            benefit_key=str(benefit.benefit_key),
            title=benefit.title,
            partner=PartnerDTO(id=partner.id, name=partner.name),
            target_university_id=benefit.target_university_id,
            target_course_id=benefit.target_course_id,
        )


@dataclass(frozen=True)
class BenefitListDTO:
    data: list[BenefitDTO]
    next_cursor: int | None

    @classmethod
    def from_models(
        cls,
        benefits: list[tuple[Benefit, Partner]],
        next_cursor: int | None
    ) -> "BenefitListDTO":
        return cls(
            data=[BenefitDTO.from_models(benefit, partner) for benefit, partner in benefits],
            next_cursor=next_cursor
        )


@dataclass(frozen=True)
class InsuranceContractedDTO:
    policy_number: str

    @classmethod
    def from_model(cls, contract: ContractedInsurance) -> "InsuranceContractedDTO":
        return cls(policy_number=str(contract.policy_number))


@dataclass(frozen=True)
class SplitBillCreatedDTO:
    status: str = "Divisão registrada com sucesso."


@dataclass(frozen=True)
class TransactionCreatedDTO:
    transaction_key: str

    @classmethod
    def from_model(cls, transaction: Transaction) -> "TransactionCreatedDTO":
        return cls(transaction_key=str(transaction.transaction_key))


@dataclass(frozen=True)
class TransactionStatementItemDTO:
    transaction_key: str
    type: str
    amount: int
    created_at: str

    @classmethod
    def from_model(
        cls,
        transaction: Transaction,
        account_id: int,
    ) -> "TransactionStatementItemDTO":
        transaction_type = "DEBIT" if transaction.origin_account_id == account_id else "CREDIT"
        return cls(
            transaction_key=str(transaction.transaction_key),
            type=transaction_type,
            amount=transaction.amount,
            created_at=transaction.created_at.isoformat(),
        )


@dataclass(frozen=True)
class TransactionStatementDTO:
    data: list[TransactionStatementItemDTO]
    next_cursor: int | None

    @classmethod
    def from_models(
        cls,
        account_id: int,
        transactions: list[Transaction],
    ) -> "TransactionStatementDTO":
        return cls(
            data=[
                TransactionStatementItemDTO.from_model(transaction, account_id)
                for transaction in transactions
            ],
            next_cursor=transactions[-1].id if transactions else None,
        )