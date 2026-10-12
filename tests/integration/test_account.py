import pytest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID
from tests.utils.random_generator import RandomGenerator
from database import SessionLocal
from models.account import Account, AccountStatus, AccountStatusEvent

MOCK_CONNECTOR_PATH = "connectors.university_connector.UniversityConnector.send"

@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=200))
def test_account_creates_successfully(mock_send, client):
    """Garante que uma conta bancária é criada com sucesso."""
    
    cpf_1 = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    customer_response = client.post("/customers", json={
        "document": cpf_1,
        "university_id": 1,
        "course_id": 1
    })
    
    assert customer_response.status_code == 201, f"Erro ao criar cliente 1: {customer_response.text}"
    customer_key = customer_response.json()["customer_key"]

    response_checking = client.post("/accounts", json={
        "customer_key": customer_key,
        "type_id": 1
    })
    assert response_checking.status_code == 201
    assert "account_key" in response_checking.json()
    checking_key = UUID(response_checking.json()["account_key"])

    with SessionLocal() as session:
        checking_account = session.query(Account).filter_by(account_key=checking_key).one()
        initial_event = session.query(AccountStatusEvent).filter_by(account_id=checking_account.id).one()
        initial_status = session.get(AccountStatus, checking_account.status_id)
        assert checking_account.type_id == 1
        assert checking_account.balance == 0
        assert initial_status.name == "ACTIVE"
        assert initial_event.from_status_id is None
        assert initial_event.to_status_id == checking_account.status_id

    cpf_2 = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    customer_response_2 = client.post("/customers", json={
        "document": cpf_2,
        "university_id": 1,
        "course_id": 1
    })
    
    assert customer_response_2.status_code == 201, f"Erro ao criar cliente 2: {customer_response_2.text}"
    customer_key_2 = customer_response_2.json()["customer_key"]

    response_savings = client.post("/accounts", json={
        "customer_key": customer_key_2,
        "type_id": 2
    })
    assert response_savings.status_code == 201
    assert "account_key" in response_savings.json()
    assert response_savings.json()["account_key"] != response_checking.json()["account_key"]


def test_account_refuses_nonexistent_customer(client):
    """Garante que a API retorna 404 ao tentar criar conta para um customer_key inexistente."""
    fake_uuid = "12345678-1234-5678-1234-567812345678"
    
    response = client.post("/accounts", json={
        "customer_key": fake_uuid,
        "type_id": 1
    })
    
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "QIT001101"  # CustomerNotFoundError


def test_account_refuses_invalid_schema_missing_fields(client):
    """Garante que o SchemaHandler barra requisições com campos obrigatórios faltando (400)."""
    response = client.post("/accounts", json={
        "type_id": 1
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "QIT000001"  # InvalidSchema


def test_account_refuses_invalid_schema_wrong_types(client):
    """Garante que o SchemaHandler barra tipos de dados incorretos no payload (400)."""
    response = client.post("/accounts", json={
        "customer_key": "12345678-1234-5678-1234-567812345678",
        "type_id": "nao-e-um-inteiro"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "QIT000001"  # InvalidSchema


def test_account_refuses_additional_properties(client):
    """Garante que campos extras não mapeados no schema são rejeitados."""
    response = client.post("/accounts", json={
        "customer_key": "12345678-1234-5678-1234-567812345678",
        "type_id": 1,
        "campo_proibido": "surpresa"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "QIT000001"


@pytest.mark.parametrize("payload", [
    {"customer_key": "not-a-uuid", "type_id": 1},
    {"customer_key": "12345678-1234-5678-1234-567812345678", "type_id": 0},
    {"customer_key": "12345678-1234-5678-1234-567812345678", "type_id": -1},
    {"customer_key": "12345678-1234-5678-1234-567812345678", "type_id": True},
])
def test_account_refuses_invalid_uuid_and_type_id_values(client, payload):
    response = client.post("/accounts", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


@pytest.mark.parametrize("token", [None, "token-incorreto"])
def test_account_requires_internal_token(client, token):
    if token is None:
        client.headers.pop("INTERNAL-TOKEN")
    else:
        client.headers["INTERNAL-TOKEN"] = token

    response = client.post("/accounts", json={})

    assert response.status_code == 403
    assert response.json()["code"] == "QIT000002"


@patch("controllers.account_controller.AccountRepository.get_status_by_name", return_value=None)
@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=200))
def test_account_refuses_creation_when_active_status_is_missing(mock_send, mock_status, client):
    customer_response = client.post("/customers", json={
        "document": RandomGenerator.generate_cpf().replace(".", "").replace("-", ""),
        "university_id": 1,
        "course_id": 1,
    })
    assert customer_response.status_code == 201

    response = client.post("/accounts", json={
        "customer_key": customer_response.json()["customer_key"],
        "type_id": 1,
    })

    assert response.status_code == 500
    assert response.json()["code"] == "QIT001500"
    mock_send.assert_called_once()
    mock_status.assert_called_once_with("ACTIVE")