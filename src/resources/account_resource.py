from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from controllers.account_controller import AccountController
from utils.schema_handler import SchemaHandler

class AccountResource:
    @SchemaHandler.validate("create_account.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = AccountController(class_name=__name__)
        result = controller.create_account(payload)
        
        return JSONResponse(
            content=jsonable_encoder(result), 
            status_code=status.HTTP_201_CREATED
        )