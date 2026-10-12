from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import (
    HealthCheckResource,
    AccountResource,
    BenefitResource,
    InsuranceResource,
    TransactionResource,
    CustomerResource
)
from utils.logger import setup_logging


def create_app() -> FastAPI:
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    register_session_manager_middleware(application)
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    health_check_resource = HealthCheckResource()
    account_resource = AccountResource()
    benefit_resource = BenefitResource()
    insurance_resource = InsuranceResource()
    transaction_resource = TransactionResource()
    customer_resource = CustomerResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route("/health_check", health_check_resource.on_get_health_check, methods=["GET"])

    application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])

    application.add_api_route("/accounts", account_resource.on_post, methods=["POST"])

    application.add_api_route("/benefits", benefit_resource.on_get_list, methods=["GET"])
    application.add_api_route("/benefits/{key}/redemptions", benefit_resource.on_post_redeem, methods=["POST"])

    application.add_api_route("/insurances", insurance_resource.on_post, methods=["POST"])

    application.add_api_route("/transactions", transaction_resource.on_post, methods=["POST"])
    application.add_api_route("/transactions/{transaction_key}/splits", transaction_resource.on_post_split, methods=["POST"])
    
    application.add_api_route("/accounts/{account_key}/transactions", transaction_resource.on_get_statement, methods=["GET"])

    register_error_handlers(application)

    return application

def main() -> FastAPI:
    check_variables()
    error_verification()
    setup_logging()
    return create_app()

app = main()