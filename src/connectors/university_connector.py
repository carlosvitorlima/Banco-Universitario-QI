import os
from connectors.rest_connector import BaseConnectorResponse, RestConnector

class UniversityConnector(RestConnector):
    def __init__(self):
        super().__init__(
            class_name=__name__,
            base_url=os.environ.get("UNIVERSITY_API_URL", "http://localhost:8081"),
            timeout=5,
            internal_token=os.environ.get("UNIVERSITY_API_TOKEN", "default_token")
        )

    def check_student_enrollment(
        self,
        document: str,
        university_id: int,
    ) -> BaseConnectorResponse:
        return self.send(
            endpoint=f"/universities/{university_id}/students/{document}",
            method="GET",
        )