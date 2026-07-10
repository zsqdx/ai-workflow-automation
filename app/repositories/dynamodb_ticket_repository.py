import os
from datetime import datetime, timezone
from typing import Optional

import boto3


class DynamoDBTicketRepository:
    def __init__(self):
        self.table_name = (
            os.getenv("TICKET_TABLE_NAME")
            or os.getenv("DYNAMODB_TICKETS_TABLE")
            or "tickets"
        )
        self.region_name = os.getenv("AWS_REGION") or "us-west-2"
        self._table = None

    def create_ticket(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        message: str,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "customer_email": customer_email,
            "message": message,
            "status": "CREATED",
            "workflow_run_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self.table.put_item(Item=ticket)
        return ticket

    def update_status(
        self,
        ticket_id: str,
        status: str,
        workflow_run_id: Optional[str] = None,
    ) -> Optional[dict]:
        now = datetime.now(timezone.utc).isoformat()
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": status,
            ":updated_at": now,
        }

        if workflow_run_id is not None:
            update_expression += ", workflow_run_id = :workflow_run_id"
            expression_attribute_values[":workflow_run_id"] = workflow_run_id

        self.table.update_item(
            Key={"ticket_id": ticket_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )
        return self.find_by_id(ticket_id)

    def find_by_id(self, ticket_id: str) -> Optional[dict]:
        response = self.table.get_item(Key={"ticket_id": ticket_id})
        return response.get("Item")

    @property
    def table(self):
        if self._table is None:
            dynamodb = boto3.resource(
                "dynamodb",
                region_name=self.region_name,
            )
            self._table = dynamodb.Table(self.table_name)
        return self._table
