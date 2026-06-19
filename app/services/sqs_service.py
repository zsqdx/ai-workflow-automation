import json
import os
from typing import List

import boto3


class SQSService:
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION") or "us-west-2"
        self.queue_url = os.getenv("WORKFLOW_QUEUE_URL")
        self.client = boto3.client("sqs", region_name=self.region_name)

    def send_refund_workflow_message(
        self,
        workflow_run_id: str,
        ticket_id: str,
        workflow_id: str,
        customer_id: str,
        order_id: str,
    ) -> str:
        message_body = {
            "event_type": "WORKFLOW_RUN_CREATED",
            "workflow_run_id": workflow_run_id,
            "ticket_id": ticket_id,
            "workflow_id": workflow_id,
            "job_type": "REFUND_JOB",
            "customer_id": customer_id,
            "order_id": order_id,
        }

        response = self.client.send_message(
            QueueUrl=self._require_queue_url(),
            MessageBody=json.dumps(message_body),
        )
        return response["MessageId"]

    def receive_messages(self, max_messages: int = 5) -> List[dict]:
        response = self.client.receive_message(
            QueueUrl=self._require_queue_url(),
            MaxNumberOfMessages=max(1, min(max_messages, 10)),
            WaitTimeSeconds=10,
        )
        return response.get("Messages", [])

    def delete_message(self, receipt_handle: str) -> None:
        self.client.delete_message(
            QueueUrl=self._require_queue_url(),
            ReceiptHandle=receipt_handle,
        )

    def _require_queue_url(self) -> str:
        if not self.queue_url:
            raise RuntimeError("WORKFLOW_QUEUE_URL is not set")
        return self.queue_url


sqs_service = SQSService()
