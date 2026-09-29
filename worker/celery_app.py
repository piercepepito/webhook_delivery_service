from celery import Celery


celery_app = Celery("webhook_delivery_service",
                    broker = "redis://localhost:6379/0",
                    backend = "redis://localhost:6379/0",
                    include=["worker.tasks"])