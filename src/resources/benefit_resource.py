from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from controllers.benefit_controller import BenefitController
from utils.schema_handler import SchemaHandler

class BenefitResource:
    @SchemaHandler.validate_query_params("get_benefits.json")
    def on_get_list(self, request: Request) -> JSONResponse:
        limit = int(request.query_params.get("limit", 10))
        cursor_str = request.query_params.get("cursor")
        cursor = int(cursor_str) if cursor_str else None

        controller = BenefitController(class_name=__name__)
        result = controller.list_benefits(limit, cursor)

        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status.HTTP_200_OK,
        )

    @SchemaHandler.validate("redeem_benefit.json")
    def on_post_redeem(self, key: UUID, payload: dict) -> JSONResponse:
        controller = BenefitController(class_name=__name__)
        
        result = controller.redeem_benefit(
            benefit_key=str(key),
            payload=payload
        )
        
        return JSONResponse(
            content=jsonable_encoder(result), 
            status_code=status.HTTP_201_CREATED
        )