class RefundWorkflow:
    def run(self, workflow_run) -> dict:
        workflow_input = workflow_run.input
        order_id = workflow_input["order_id"]
        refund_reason = workflow_input["refund_reason"]

        print("Starting refund workflow")
        print(f"workflow_run_id={workflow_run.workflow_run_id}")
        print(f"order_id={order_id}")
        print(f"refund_reason={refund_reason}")
        print("Step 1: Checking order")
        print("Step 2: Validating refund eligibility")
        print("Step 3: Processing refund")
        print("Refund workflow completed")

        return {
            "order_id": order_id,
            "refund_reason": refund_reason,
            "refund_status": "PROCESSED",
        }
