from uuid import UUID, uuid4
from unittest.mock import patch
from types import SimpleNamespace

from database import SessionLocal
from models.account import Account
from tests.utils.random_generator import RandomGenerator


def create_customer(client, university_id: int = 1, course_id: int = 1) -> str:
    payload = {
        "document": RandomGenerator.generate_cpf().replace(".", "").replace("-", ""),
        "university_id": university_id,
        "course_id": course_id,
    }
    with patch(
        "connectors.university_connector.UniversityConnector.send",
        return_value=SimpleNamespace(status=200),
    ):
        response = client.post("/customers", json=payload)

    assert response.status_code == 201, response.text
    return response.json()["customer_key"]


def create_account(client, customer_key: str, type_id: int = 1) -> str:
    response = client.post("/accounts", json={
        "customer_key": customer_key,
        "type_id": type_id,
    })
    assert response.status_code == 201, response.text
    return response.json()["account_key"]


def set_account_balance(account_key: str, balance: int) -> None:
    with SessionLocal() as session:
        account = session.query(Account).filter_by(account_key=UUID(account_key)).one()
        account.balance = balance
        session.commit()


def create_transfer(client, origin_key: str, destination_key: str, amount: int) -> dict:
    response = client.post("/transactions", json={
        "idempotency_key": f"transfer-{uuid4()}",
        "origin_account_key": origin_key,
        "destination_account_key": destination_key,
        "amount": amount,
    })
    assert response.status_code == 201, response.text
    return response.json()