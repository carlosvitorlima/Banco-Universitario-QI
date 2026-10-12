import pytest
from uuid import uuid4
from database import SessionLocal
from models.insurance import Insurance
from tests.utils.api_helpers import create_customer


def _create_insurance():
    with SessionLocal() as session:
        insurance = Insurance(name=f"Insurance {uuid4()}", monthly_premium=100)
        session.add(insurance)
        session.commit()
        return insurance.id


def test_insurance_contract_successfully(client):
    """Garante que um cliente consegue contratar um seguro elegível com sucesso."""
    customer_key = create_customer(client)
    insurance_id = _create_insurance()

    response = client.post("/insurances", json={
        "customer_key": customer_key,
        "insurance_id": insurance_id
    })

    assert response.status_code == 201
    assert len(response.json()["policy_number"]) == 36


def test_insurance_refuses_nonexistent_customer(client):
    """Garante que a API retorna 404 ao tentar contratar seguro para um customer_key inexistente."""
    fake_customer_key = "12345678-1234-5678-1234-567812345678"

    response = client.post("/insurances", json={
        "customer_key": fake_customer_key,
        "insurance_id": 1
    })

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001101"


def test_insurance_refuses_invalid_schema(client):
    """Garante que o SchemaHandler barra requisições com campos obrigatórios faltando (400)."""
    response = client.post("/insurances", json={
        "insurance_id": 1
    })

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_insurance_refuses_unknown_insurance(client):
    customer_key = create_customer(client)

    response = client.post("/insurances", json={
        "customer_key": customer_key,
        "insurance_id": 2147483647,
    })

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001104"


def test_insurance_refuses_duplicate_contract(client):
    customer_key = create_customer(client)
    insurance_id = _create_insurance()
    payload = {"customer_key": customer_key, "insurance_id": insurance_id}

    first_response = client.post("/insurances", json=payload)
    second_response = client.post("/insurances", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "QIT001411"


@pytest.mark.parametrize("payload", [
    {"customer_key": "not-a-uuid", "insurance_id": 1},
    {"customer_key": "12345678-1234-5678-1234-567812345678", "insurance_id": 0},
    {"customer_key": "12345678-1234-5678-1234-567812345678", "insurance_id": True},
])
def test_insurance_refuses_invalid_field_values(client, payload):
    response = client.post("/insurances", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"