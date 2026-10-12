from uuid import UUID, uuid4

import pytest

from database import SessionLocal
from models.account import Account
from models.transaction import Transaction
from tests.utils.api_helpers import (
    create_account,
    create_customer,
    create_transfer,
    set_account_balance,
)

def test_transaction_schema_refuses_empty_body(client):
    """
    Um payload vazio deve ser barrado pelo SchemaHandler antes de chegar ao Controller.
    """
    payload = {}
    
    response = client.post("/transactions", json=payload)
    response_json = response.json()
    
    assert response.status_code == 400
    assert response_json["code"] == "QIT000001"

def test_transaction_schema_refuses_negative_amount(client):
    """
    O schema deve garantir que o valor (amount) seja estritamente positivo (minimum: 1).
    """
    payload = {
        "idempotency_key": "transfer-valid-key",
        "origin_account_key": "12345678-1234-5678-1234-567812345678",
        "destination_account_key": "87654321-4321-4321-4321-876543210987",
        "amount": -50
    }
    
    response = client.post("/transactions", json=payload)
    
    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"

@pytest.mark.parametrize("invalid_fields", [
    {"amount": 0},
    {"amount": True},
    {"idempotency_key": "tiny"},
    {"origin_account_key": "invalid-uuid"},
    {"unexpected": "field"},
])
def test_transaction_schema_refuses_invalid_field_values(client, invalid_fields):
    payload = {
        "idempotency_key": "transfer-valid-key",
        "origin_account_key": "12345678-1234-5678-1234-567812345678",
        "destination_account_key": "87654321-4321-4321-4321-876543210987",
        "amount": 25,
    }
    payload.update(invalid_fields)

    response = client.post("/transactions", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_transaction_transfers_funds_and_persists_record(client):
    origin_customer_key = create_customer(client)
    destination_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    destination_key = create_account(client, destination_customer_key)
    set_account_balance(origin_key, 300)

    response = client.post("/transactions", json={
        "idempotency_key": f"successful-transfer-{uuid4()}",
        "origin_account_key": origin_key,
        "destination_account_key": destination_key,
        "amount": 125,
    })

    assert response.status_code == 201
    transaction_key = UUID(response.json()["transaction_key"])
    with SessionLocal() as session:
        origin = session.query(Account).filter_by(account_key=UUID(origin_key)).one()
        destination = session.query(Account).filter_by(account_key=UUID(destination_key)).one()
        transaction = session.query(Transaction).filter_by(transaction_key=transaction_key).one()
        assert origin.balance == 175
        assert destination.balance == 125
        assert transaction.amount == 125


def test_transaction_refuses_when_accounts_do_not_exist(client):
    response = client.post("/transactions", json={
        "idempotency_key": "missing-account-transfer",
        "origin_account_key": "12345678-1234-5678-1234-567812345678",
        "destination_account_key": "87654321-4321-4321-4321-876543210987",
        "amount": 10,
    })

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001102"


def test_transaction_refuses_same_origin_and_destination(client):
    account_key = "12345678-1234-5678-1234-567812345678"
    response = client.post("/transactions", json={
        "idempotency_key": f"same-account-transfer-{uuid4()}",
        "origin_account_key": account_key,
        "destination_account_key": account_key,
        "amount": 1,
    })

    assert response.status_code == 400
    assert response.json()["code"] == "QIT001429"


def test_transaction_refuses_insufficient_balance(client):
    origin_customer_key = create_customer(client)
    destination_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    destination_key = create_account(client, destination_customer_key)

    response = client.post("/transactions", json={
        "idempotency_key": "insufficient-balance-transfer",
        "origin_account_key": origin_key,
        "destination_account_key": destination_key,
        "amount": 1,
    })

    assert response.status_code == 422
    assert response.json()["code"] == "QIT001427"


def test_transaction_rejects_reused_idempotency_key_without_second_debit(client):
    origin_customer_key = create_customer(client)
    destination_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    destination_key = create_account(client, destination_customer_key)
    set_account_balance(origin_key, 200)
    payload = {
        "idempotency_key": f"same-idempotency-key-{uuid4()}",
        "origin_account_key": origin_key,
        "destination_account_key": destination_key,
        "amount": 50,
    }

    first_response = client.post("/transactions", json=payload)
    second_response = client.post("/transactions", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "QIT001412"
    with SessionLocal() as session:
        origin = session.query(Account).filter_by(account_key=UUID(origin_key)).one()
        destination = session.query(Account).filter_by(account_key=UUID(destination_key)).one()
        assert origin.balance == 150
        assert destination.balance == 50


def test_transaction_statement_refuses_unknown_account(client):
    response = client.get("/accounts/12345678-1234-5678-1234-567812345678/transactions")

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001102"


def test_transaction_statement_formats_debits_credits_and_cursor(client):
    origin_customer_key = create_customer(client)
    first_destination_customer_key = create_customer(client)
    second_destination_customer_key = create_customer(client)
    empty_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    first_destination_key = create_account(client, first_destination_customer_key)
    second_destination_key = create_account(client, second_destination_customer_key)
    empty_account_key = create_account(client, empty_customer_key)
    set_account_balance(origin_key, 100)
    create_transfer(client, origin_key, first_destination_key, 40)
    create_transfer(client, origin_key, second_destination_key, 30)

    first_response = client.get(f"/accounts/{origin_key}/transactions", params={"limit": 1})
    assert first_response.status_code == 200
    first_page = first_response.json()
    second_page = client.get(
        f"/accounts/{origin_key}/transactions",
        params={"limit": 10, "cursor": first_page["next_cursor"]},
    ).json()
    credit_statement = client.get(
        f"/accounts/{first_destination_key}/transactions",
        params={"limit": 10},
    ).json()
    empty_statement = client.get(
        f"/accounts/{empty_account_key}/transactions",
        params={"limit": 10},
    ).json()

    assert first_page["data"][0]["type"] == "DEBIT"
    assert first_page["data"][0]["amount"] == 40
    assert isinstance(first_page["next_cursor"], int)
    assert second_page["data"][0]["type"] == "DEBIT"
    assert second_page["data"][0]["amount"] == 30
    assert credit_statement["data"][0]["type"] == "CREDIT"
    assert credit_statement["data"][0]["amount"] == 40
    assert empty_statement == {"data": [], "next_cursor": None}


@pytest.mark.parametrize("params", [
    {"limit": 0},
    {"limit": 101},
    {"cursor": 0},
    {"cursor": "invalid"},
])
def test_transaction_statement_refuses_invalid_pagination_params(client, params):
    response = client.get(
        "/accounts/12345678-1234-5678-1234-567812345678/transactions",
        params=params,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000010"


def test_transaction_statement_refuses_invalid_account_key_format(client):
    response = client.get("/accounts/not-a-uuid/transactions")

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000010"