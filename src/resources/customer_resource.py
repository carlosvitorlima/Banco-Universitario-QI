from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from controllers.customer_controller import CustomerController
from utils.schema_handler import SchemaHandler

class CustomerResource:
    @SchemaHandler.validate("create_customer.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = CustomerController(class_name=__name__)
        
        result = controller.create_customer(payload=payload)
        
        return JSONResponse(
            content=jsonable_encoder(result), 
            status_code=status.HTTP_201_CREATED
        )