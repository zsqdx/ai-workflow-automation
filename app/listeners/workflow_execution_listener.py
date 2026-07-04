import json
import os
import time

from app.schemas.workflow_run import WorkflowRunStatus
from app.services.sqs_service import sqs_service
from app.services.workflow_run_service import workflow_run_service
from app.workflows.refund_workflow import RefundWorkflow


class WorkflowExecutionListener:
    def __init__(
        self,
        sqs=sqs_service,
        workflow_runs=workflow_run_service,
        refund_workflow=None,
    ):
        self.sqs_service = sqs
        self.workflow_run_service = workflow_runs
        self.refund_workflow = refund_workflow or RefundWorkflow()

    def run_once(self):
        print("Polling SQS")
        messages = self.sqs_service.receive_messages()
        print(f"Received {len(messages)} SQS message(s)")
        if not messages:
            print("No messages found")

        for raw_message in messages:
            receipt_handle = raw_message["ReceiptHandle"]
            workflow_run_id = None
            should_mark_failed = False

            try:
                print("Received SQS message")
                message = json.loads(raw_message.get("Body", "{}"))
                workflow_run_id = message["workflow_run_id"]
                print(f"workflow_run_id={workflow_run_id}")

                workflow_run = self.workflow_run_service.get_workflow_run(
                    workflow_run_id
                )
                print("Loaded workflow_run")
                print(f"Current status={workflow_run.status.value}")

                if self.workflow_run_service.should_skip_execution(workflow_run_id):
                    print(
                        f"workflow_run_id={workflow_run_id} already completed. "
                        "Skipping duplicate message."
                    )
                    self.sqs_service.delete_message(receipt_handle)
                    print("SQS message deleted")
                    continue

                if workflow_run.status not in {
                    WorkflowRunStatus.PENDING,
                    WorkflowRunStatus.FAILED,
                }:
                    print(
                        f"workflow_run_id={workflow_run_id} status="
                        f"{workflow_run.status.value}; skipping for now"
                    )
                    continue

                if workflow_run.workflow_type != "REFUND_WORKFLOW":
                    self.workflow_run_service.update_status(
                        workflow_run_id,
                        WorkflowRunStatus.FAILED.value,
                        error_message=(
                            f"Unknown workflow_type: {workflow_run.workflow_type}"
                        ),
                    )
                    print("Updated status to FAILED")
                    print("SQS message not deleted")
                    continue

                self.workflow_run_service.update_status(
                    workflow_run_id,
                    WorkflowRunStatus.RUNNING.value,
                )
                should_mark_failed = True
                print("Updated status to RUNNING")

                self.refund_workflow.run(workflow_run)

                self.workflow_run_service.update_status(
                    workflow_run_id,
                    WorkflowRunStatus.SUCCEEDED.value,
                )
                should_mark_failed = False
                print("Updated status to SUCCEEDED")

                self.sqs_service.delete_message(receipt_handle)
                print("SQS message deleted")
            except Exception as exc:
                print(f"Workflow execution failed: {exc}")
                if workflow_run_id is not None and should_mark_failed:
                    try:
                        self.workflow_run_service.update_status(
                            workflow_run_id,
                            WorkflowRunStatus.FAILED.value,
                            error_message=str(exc),
                        )
                        print("Updated status to FAILED")
                    except Exception as status_exc:
                        print(f"Failed to update workflow_run status: {status_exc}")
                print("SQS message not deleted")

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(5)


if __name__ == "__main__":
    print("Listener started")
    listener = WorkflowExecutionListener()
    if os.getenv("LISTENER_RUN_ONCE", "").lower() == "true":
        listener.run_once()
    else:
        listener.run_forever()
