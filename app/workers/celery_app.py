from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

celery = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    include=["app.workers.tasks"]
)