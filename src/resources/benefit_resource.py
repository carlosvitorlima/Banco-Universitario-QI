from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from controllers.benefit_controller import BenefitController
from utils.schema_handler import SchemaHandler

class BenefitResource:
    def on_get_list(self) -> JSONResponse:
        controller = BenefitController(class_name=__name__)
        result = controller.list_benefits()

        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status.HTTP_200_OK,
        )

    @SchemaHandler.validate("redeem_benefit.json")
    def on_post_redeem(self, key: str, payload: dict) -> JSONResponse:
        controller = BenefitController(class_name=__name__)
        
        result = controller.redeem_benefit(
            benefit_key=key, 
            payload=payload
        )
        
        return JSONResponse(
            content=jsonable_encoder(result), 
            status_code=status.HTTP_201_CREATED
        )