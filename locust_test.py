from locust import HttpUser, task, between
import random
import datetime

class LoadTest(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:5000"

    @task
    def add_shift(self):
        shift_data = {
            "employee_id": random.randint(1, 1000),
            "date": datetime.date.today().isoformat(),
            "start_time": "09:00",
            "end_time": "17:00"
        }
        self.client.post("/add_shift", json=shift_data)
