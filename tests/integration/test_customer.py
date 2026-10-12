import pytest
from types import SimpleNamespace
from unittest.mock import patch
from requests.exceptions import Timeout
from tests.utils.random_generator import RandomGenerator

MOCK_CONNECTOR_PATH = "connectors.university_connector.UniversityConnector.send"

def test_customer_schema_refuses_invalid_document_format(client):
    """O schema exige que o documento tenha exatamente 11 dígitos numéricos."""
    payload = {
        "document": "12345",
        "university_id": 1,
        "course_id": 1
    }
    
    response = client.post("/customers", json=payload)
    
    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_customer_refuses_invalid_cpf_math(client):
    """O documento passa no schema (11 dígitos), mas falha na conta matemática do CPF."""
    payload = {
        "document": "11111111111",
        "university_id": 1,
        "course_id": 1
    }
    
    response = client.post("/customers", json=payload)
    
    assert response.status_code == 422
    assert response.json()["code"] == "QIT001424"


@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=404))
def test_customer_refuses_invalid_academic_bond(mock_send, client):
    """O CPF é válido, mas a API da universidade diz que o aluno NÃO está matriculado."""
    clean_cpf = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    
    payload = {
        "document": clean_cpf,
        "university_id": 1,
        "course_id": 1
    }
    
    response = client.post("/customers", json=payload)
    
    assert response.status_code == 422
    assert response.json()["code"] == "QIT001425"


@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=200))
def test_customer_creates_successfully(mock_send, client):
    """Caminho Feliz: CPF válido e aluno matriculado na universidade."""
    
    clean_cpf = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    
    payload = {
        "document": clean_cpf,
        "university_id": 1,
        "course_id": 1
    }
    
    response = client.post("/customers", json=payload)
    
    assert response.status_code == 201
    assert "customer_key" in response.json()


@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=200))
def test_customer_refuses_duplicated_document(mock_send, client):
    """Garante que a API barra com 409 o cadastro de um mesmo CPF duas vezes."""
    clean_cpf = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    
    payload = {
        "document": clean_cpf,
        "university_id": 1,
        "course_id": 1
    }
    
    response_1 = client.post("/customers", json=payload)
    assert response_1.status_code == 201
    
    response_2 = client.post("/customers", json=payload)
    assert response_2.status_code == 409
    assert response_2.json()["code"] == "QIT001410"


@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=503))
def test_customer_reports_university_api_error(mock_send, client):
    response = client.post("/customers", json={
        "document": RandomGenerator.generate_cpf().replace(".", "").replace("-", ""),
        "university_id": 1,
        "course_id": 1,
    })

    assert response.status_code == 502
    assert response.json()["code"] == "QIT001502"
    mock_send.assert_called_once()


@patch(MOCK_CONNECTOR_PATH, side_effect=Timeout)
def test_customer_reports_university_api_timeout(mock_send, client):
    response = client.post("/customers", json={
        "document": RandomGenerator.generate_cpf().replace(".", "").replace("-", ""),
        "university_id": 1,
        "course_id": 1,
    })

    assert response.status_code == 504
    assert response.json()["code"] == "QIT001504"
    mock_send.assert_called_once()


@pytest.mark.parametrize("payload", [
    {"university_id": 1, "course_id": 1},
    {"document": "12345678901", "university_id": True, "course_id": 1},
    {"document": "12345678901", "university_id": 1, "course_id": 1, "extra": "x"},
])
def test_customer_schema_refuses_missing_wrong_type_and_extra_fields(client, payload):
    response = client.post("/customers", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"