import pytest
from uuid import UUID

from database import SessionLocal
from models.split_bill import SplitBill
from models.transaction import Transaction
from tests.utils.api_helpers import (
    create_account,
    create_customer,
    create_transfer,
    set_account_balance,
)

def test_split_bill_refuses_nonexistent_transaction(client):
    """Garante que a API retorna 404 ao tentar dividir uma transação que não existe."""
    fake_transaction_key = "12345678-1234-5678-1234-567812345678"
    
    response = client.post(f"/transactions/{fake_transaction_key}/splits", json={
        "splits": [
            {"account_key": "12345678-1234-5678-1234-567812345678", "amount": 100}
        ]
    })
    
    assert response.status_code == 404
    assert response.json()["code"] == "QIT001105"


def test_split_bill_refuses_mismatched_amounts(client):
    """Garante que a soma das fatias precisa ser igual ao total transferido."""
    origin_customer_key = create_customer(client)
    destination_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    destination_key = create_account(client, destination_customer_key)
    set_account_balance(origin_key, 100)
    transaction = create_transfer(client, origin_key, destination_key, 100)

    response = client.post(f"/transactions/{transaction['transaction_key']}/splits", json={
        "splits": [{"account_key": destination_key, "amount": 99}],
    })

    assert response.status_code == 422
    assert response.json()["code"] == "QIT001428"


def test_split_bill_refuses_invalid_split_items(client):
    """Garante que cada item exige account_key e amount."""
    fake_transaction_key = "12345678-1234-5678-1234-567812345678"
    
    response = client.post(f"/transactions/{fake_transaction_key}/splits", json={
        "splits": [{"account_key": "12345678-1234-5678-1234-567812345678"}]
    })
    
    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_split_bill_refuses_missing_splits(client):
    """Garante que o SchemaHandler exige a lista splits."""
    fake_transaction_key = "12345678-1234-5678-1234-567812345678"
    
    response = client.post(f"/transactions/{fake_transaction_key}/splits", json={
        "splits": []
    })
    
    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_split_bill_refuses_duplicate_payer_accounts(client):
    duplicate_account_key = "12345678-1234-5678-1234-567812345678"

    response = client.post("/transactions/87654321-4321-4321-4321-876543210987/splits", json={
        "splits": [
            {"account_key": duplicate_account_key, "amount": 50},
            {"account_key": duplicate_account_key, "amount": 50},
        ]
    })

    assert response.status_code == 400
    assert response.json()["code"] == "QIT001400"


def test_split_bill_refuses_unknown_payer_accounts(client):
    origin_customer_key = create_customer(client)
    destination_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    destination_key = create_account(client, destination_customer_key)
    set_account_balance(origin_key, 100)
    transaction = create_transfer(client, origin_key, destination_key, 100)

    response = client.post(f"/transactions/{transaction['transaction_key']}/splits", json={
        "splits": [{
            "account_key": "12345678-1234-5678-1234-567812345678",
            "amount": 100,
        }],
    })

    assert response.status_code == 422
    assert response.json()["code"] == "QIT001426"


def test_split_bill_creates_splits_when_amounts_match(client):
    origin_customer_key = create_customer(client)
    first_payer_customer_key = create_customer(client)
    second_payer_customer_key = create_customer(client)
    origin_key = create_account(client, origin_customer_key)
    first_payer_key = create_account(client, first_payer_customer_key)
    second_payer_key = create_account(client, second_payer_customer_key)
    set_account_balance(origin_key, 120)
    transaction = create_transfer(client, origin_key, first_payer_key, 120)

    response = client.post(f"/transactions/{transaction['transaction_key']}/splits", json={
        "splits": [
            {"account_key": first_payer_key, "amount": 50},
            {"account_key": second_payer_key, "amount": 70},
        ],
    })

    assert response.status_code == 201
    assert response.json()["status"] == "Divisão registrada com sucesso."
    with SessionLocal() as session:
        transaction_row = session.query(Transaction).filter_by(
            transaction_key=UUID(transaction["transaction_key"])
        ).one()
        splits = session.query(SplitBill).filter_by(transaction_id=transaction_row.id).all()
        assert sorted(split.amount for split in splits) == [50, 70]