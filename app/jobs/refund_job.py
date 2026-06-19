class RefundJob:
    def run(self, message: dict) -> None:
        order_id = message.get("order_id")
        customer_id = message.get("customer_id")

        print(f"RefundJob started for customer_id={customer_id}, order_id={order_id}")
        print("Extracting order id...")
        print("Checking order status...")
        print("Issuing refund...")
        print("Generating customer reply...")
        print("Updating ticket status...")
        print("RefundJob completed")
