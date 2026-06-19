import json
import os
import time

from app.jobs.job_dispatcher import job_dispatcher
from app.schemas.workflow_run import WorkflowRunStatus
from app.services.sqs_service import sqs_service
from app.services.workflow_run_service import workflow_run_service


class RefundWorker:
    def __init__(
        self,
        sqs=sqs_service,
        workflow_runs=workflow_run_service,
        dispatcher=job_dispatcher,
    ):
        self.sqs_service = sqs
        self.workflow_run_service = workflow_runs
        self.job_dispatcher = dispatcher

    def run_once(self):
        messages = self.sqs_service.receive_messages()
        print(f"Received {len(messages)} message(s)")

        for raw_message in messages:
            receipt_handle = raw_message["ReceiptHandle"]
            workflow_run_id = None
            should_mark_failed = False

            try:
                message = json.loads(raw_message.get("Body", "{}"))
                workflow_run_id = message["workflow_run_id"]
                job_type = message["job_type"]

                print(f"Received message workflow_run_id={workflow_run_id}")
                workflow_run = self.workflow_run_service.get_workflow_run(
                    workflow_run_id
                )
                print(f"current status={workflow_run.status.value}")

                if self.workflow_run_service.should_skip_execution(workflow_run_id):
                    print(
                        f"workflow_run_id={workflow_run_id} already completed. "
                        "Skipping duplicate message."
                    )
                    self.sqs_service.delete_message(receipt_handle)
                    print("message deleted")
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

                self.workflow_run_service.update_status(
                    workflow_run_id,
                    WorkflowRunStatus.RUNNING.value,
                )
                should_mark_failed = True
                print("updated to RUNNING")

                self.job_dispatcher.dispatch(job_type, message)

                self.workflow_run_service.update_status(
                    workflow_run_id,
                    WorkflowRunStatus.SUCCEEDED.value,
                )
                should_mark_failed = False
                print("updated to SUCCEEDED")

                self.sqs_service.delete_message(receipt_handle)
                print("message deleted")
            except Exception as exc:
                print(f"Worker failed: {exc}")
                if workflow_run_id is not None and should_mark_failed:
                    try:
                        self.workflow_run_service.update_status(
                            workflow_run_id,
                            WorkflowRunStatus.FAILED.value,
                            error_message=str(exc),
                        )
                        print("updated to FAILED")
                    except Exception as status_exc:
                        print(f"Failed to update workflow_run status: {status_exc}")
                print("message not deleted")

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(5)


if __name__ == "__main__":
    worker = RefundWorker()
    if os.getenv("WORKER_RUN_ONCE", "").lower() == "true":
        worker.run_once()
    else:
        worker.run_forever()
