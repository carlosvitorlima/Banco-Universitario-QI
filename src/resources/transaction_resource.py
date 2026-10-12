from uuid import UUID

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from controllers.transaction_controller import TransactionController
from controllers.split_bill_controller import SplitBillController
from utils.schema_handler import SchemaHandler

class TransactionResource:
    
    @SchemaHandler.validate_query_params("get_statement.json")
    def on_get_statement(
        self,
        account_key: UUID,
        request: Request
    ) -> JSONResponse:
        limit = int(request.query_params.get("limit", 10))
        cursor_str = request.query_params.get("cursor")
        cursor = int(cursor_str) if cursor_str else None

        controller = TransactionController(class_name=__name__)
        result = controller.get_statement(str(account_key), limit, cursor)

        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status.HTTP_200_OK,
        )
    
    @SchemaHandler.validate("create_transaction.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = TransactionController(class_name=__name__)
        result = controller.execute_transfer(payload)
        
        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status.HTTP_201_CREATED
        )

    @SchemaHandler.validate("create_split.json")
    def on_post_split(self, transaction_key: UUID, payload: dict) -> JSONResponse:
        controller = SplitBillController(class_name=__name__)
        result = controller.create_split(str(transaction_key), payload)
        
        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status.HTTP_201_CREATED
        )