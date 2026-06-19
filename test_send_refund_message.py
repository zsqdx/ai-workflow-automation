from app.schemas.workflow_run import WorkflowRunStatus
from app.services.sqs_service import sqs_service
from app.services.workflow_run_service import workflow_run_service


def main():
    workflow_run_service.create_workflow_run(
        workflow_run_id="run_refund_123",
        ticket_id="ticket_123",
        workflow_id="wf_refund",
        job_type="REFUND_JOB",
        customer_id="c_123",
        status=WorkflowRunStatus.PENDING,
    )

    message_id = sqs_service.send_refund_workflow_message(
        workflow_run_id="run_refund_123",
        ticket_id="ticket_123",
        workflow_id="wf_refund",
        customer_id="c_123",
        order_id="O123",
    )

    print("Refund workflow message sent successfully")
    print(f"MessageId: {message_id}")


if __name__ == "__main__":
    main()
