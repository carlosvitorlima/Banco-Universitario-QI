import pytest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from database import SessionLocal
from models.benefit import Benefit, Partner
from models.customer import Course, University
from tests.utils.api_helpers import create_customer
from tests.utils.random_generator import RandomGenerator

MOCK_CONNECTOR_PATH = "connectors.university_connector.UniversityConnector.send"


def _create_benefit(target_university_id=None, target_course_id=None):
    with SessionLocal() as session:
        partner = Partner(name=f"Partner {uuid4()}")
        session.add(partner)
        session.flush()
        benefit = Benefit(
            partner_id=partner.id,
            title=f"Benefit {uuid4()}",
            target_university_id=target_university_id,
            target_course_id=target_course_id,
        )
        session.add(benefit)
        session.commit()
        return str(benefit.benefit_key)


def test_benefit_list_returns_partner_and_eligibility_targets(client):
    partner_name = f"Partner {uuid4()}"
    with SessionLocal() as session:
        partner = Partner(name=partner_name)
        session.add(partner)
        session.flush()
        partner_id = partner.id
        benefit = Benefit(
            partner_id=partner_id,
            title=f"Benefit {uuid4()}",
            target_university_id=1,
            target_course_id=None,
        )
        session.add(benefit)
        session.flush()
        benefit_key = str(benefit.benefit_key)
        benefit_title = benefit.title
        session.commit()

    response = client.get("/benefits", params={"limit": 10})
    listed_benefit = None
    while True:
        assert response.status_code == 200
        page = response.json()
        listed_benefit = next(
            (
                item for item in page["data"]
                if item["benefit_key"] == benefit_key
            ),
            None,
        )
        if listed_benefit is not None or page["next_cursor"] is None:
            break
        response = client.get(
            "/benefits",
            params={"limit": 10, "cursor": page["next_cursor"]},
        )

    assert listed_benefit is not None
    assert listed_benefit == {
        "benefit_key": benefit_key,
        "title": benefit_title,
        "partner": {"id": partner_id, "name": partner_name},
        "target_university_id": 1,
        "target_course_id": None,
    }


def test_benefit_list_requires_internal_token(client):
    client.headers.pop("INTERNAL-TOKEN")

    response = client.get("/benefits")

    assert response.status_code == 403
    assert response.json()["code"] == "QIT000002"

@patch(MOCK_CONNECTOR_PATH, return_value=SimpleNamespace(status=200))
def test_benefit_redemption_successfully(mock_send, client):

    cpf = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
    customer_response = client.post("/customers", json={
        "document": cpf,
        "university_id": 1,
        "course_id": 1
    })
    
    if customer_response.status_code == 409:
        cpf = RandomGenerator.generate_cpf().replace(".", "").replace("-", "")
        customer_response = client.post("/customers", json={
            "document": cpf,
            "university_id": 1,
            "course_id": 1
        })

    assert customer_response.status_code == 201
    customer_key = customer_response.json()["customer_key"]

    benefit_key = _create_benefit()
    response = client.post(f"/benefits/{benefit_key}/redemptions", json={
        "customer_key": customer_key
    })
    
    assert response.status_code == 201
    assert response.json()["voucher_code"].startswith("QI-")


def test_benefit_refuses_nonexistent_customer(client):
    """Garante que a API retorna 404 se tentar resgatar com um customer_key que não existe."""
    fake_benefit_key = "12345678-1234-5678-1234-567812345678"
    fake_customer_key = "87654321-4321-4321-4321-876543210987"

    response = client.post(f"/benefits/{fake_benefit_key}/redemptions", json={
        "customer_key": fake_customer_key
    })

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001101"


def test_benefit_refuses_nonexistent_benefit_for_existing_customer(client):
    customer_key = create_customer(client)
    missing_benefit_key = str(uuid4())

    response = client.post(f"/benefits/{missing_benefit_key}/redemptions", json={
        "customer_key": customer_key,
    })

    assert response.status_code == 404
    assert response.json()["code"] == "QIT001103"


def test_benefit_refuses_invalid_schema(client):
    """Garante que o SchemaHandler barra requisições sem o customer_key (400)."""
    fake_benefit_key = "12345678-1234-5678-1234-567812345678"

    response = client.post(f"/benefits/{fake_benefit_key}/redemptions", json={
    })

    assert response.status_code == 400
    assert response.json()["code"] == "QIT000001"


def test_benefit_refuses_ineligible_university(client):
    customer_key = create_customer(client)
    target_university_id = 1_000_000 + uuid4().int % 1_000_000_000
    with SessionLocal() as session:
        university = University(
            id=target_university_id,
            name=f"University {uuid4()}",
        )
        partner = Partner(name=f"Partner {uuid4()}")
        session.add_all([university, partner])
        session.flush()
        benefit = Benefit(
            partner_id=partner.id,
            title=f"Benefit {uuid4()}",
            target_university_id=university.id,
        )
        session.add(benefit)
        session.commit()
        benefit_key = str(benefit.benefit_key)

    response = client.post(f"/benefits/{benefit_key}/redemptions", json={
        "customer_key": customer_key,
    })

    assert response.status_code == 422
    assert response.json()["code"] == "QIT001422"


def test_benefit_refuses_ineligible_course(client):
    customer_key = create_customer(client)
    target_course_id = 1_000_000 + uuid4().int % 1_000_000_000
    with SessionLocal() as session:
        course = Course(
            id=target_course_id,
            name=f"Course {uuid4()}",
        )
        partner = Partner(name=f"Partner {uuid4()}")
        session.add_all([course, partner])
        session.flush()
        benefit = Benefit(
            partner_id=partner.id,
            title=f"Benefit {uuid4()}",
            target_course_id=course.id,
        )
        session.add(benefit)
        session.commit()
        benefit_key = str(benefit.benefit_key)

    response = client.post(f"/benefits/{benefit_key}/redemptions", json={
        "customer_key": customer_key,
    })

    assert response.status_code == 422
    assert response.json()["code"] == "QIT001423"


def test_benefit_refuses_duplicate_redemption(client):
    customer_key = create_customer(client)
    benefit_key = _create_benefit()
    payload = {"customer_key": customer_key}

    first_response = client.post(f"/benefits/{benefit_key}/redemptions", json=payload)
    second_response = client.post(f"/benefits/{benefit_key}/redemptions", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "QIT001409"