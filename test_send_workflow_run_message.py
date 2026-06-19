from app.schemas.workflow_run import WorkflowRunStatus
from app.services.sqs_service import sqs_service
from app.services.workflow_run_service import workflow_run_service


def main():
    workflow_run_service.create_workflow_run(
        workflow_run_id="run_refund_123",
        ticket_id="ticket_123",
        customer_id="c_123",
        workflow_id="wf_refund",
        workflow_type="REFUND_WORKFLOW",
        status=WorkflowRunStatus.PENDING,
        input={
            "order_id": "O123",
            "message": "I want a refund",
        },
    )

    message_id = sqs_service.send_workflow_run_message("run_refund_123")

    print("Workflow run message sent successfully")
    print(f"MessageId: {message_id}")


if __name__ == "__main__":
    main()
