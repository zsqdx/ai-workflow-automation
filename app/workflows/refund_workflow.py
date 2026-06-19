class RefundWorkflow:
    def run(self, workflow_run) -> None:
        order_id = workflow_run.input.get("order_id")

        print("Starting refund workflow")
        print(f"workflow_run_id={workflow_run.workflow_run_id}")
        print(f"order_id={order_id}")
        print("Step 1: Extracting order id")
        print("Step 2: Checking order status")
        print("Step 3: Issuing refund")
        print("Step 4: Generating customer reply")
        print("Step 5: Updating ticket status")
        print("Refund workflow completed")
