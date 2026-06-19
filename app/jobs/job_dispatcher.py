from app.jobs.refund_job import RefundJob


class JobDispatcher:
    def __init__(self):
        self.refund_job = RefundJob()

    def dispatch(self, job_type: str, message: dict) -> None:
        if job_type == "REFUND_JOB":
            self.refund_job.run(message)
            return

        raise ValueError(f"Unknown job_type: {job_type}")


job_dispatcher = JobDispatcher()
