from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from controllers.insurance_controller import InsuranceController
from utils.schema_handler import SchemaHandler

class InsuranceResource:
    @SchemaHandler.validate("contract_insurance.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = InsuranceController(class_name=__name__)
        
        result = controller.contract_insurance(payload=payload)
        
        return JSONResponse(
            content=jsonable_encoder(result), 
            status_code=status.HTTP_201_CREATED
        )