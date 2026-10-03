import time
from celery.result import AsyncResult

from worker.celery_app import celery_app

from sqlalchemy import delete
from db import LocalSession
import models

def wait_for_tasks(task_ids: list[str], timeout: int = 360) -> list:
    """
    Wait until all celery tasks are finished

    args:
    task_ids: celery task id
    timeout: how long should the program wait, in seconds, till it raises an error

    returns:
    - 
    """
    task_results = [
        #check the tasks status
        AsyncResult(task_id, app=celery_app) for task_id in task_ids 
    ]

    deadline = time.monotonic() + timeout

    while not all(result.ready() for result in task_results):
        if time.monotonic() > deadline:
            raise TimeoutError("Delivery task did not finish in time")

        time.sleep(1)

    return task_results

def database_cleanup():
    with LocalSession() as session:
        try:
            session.execute(delete(models.DeliveryAttempts))
            session.execute(delete(models.Deliveries))
            session.execute(delete(models.Events))
            session.execute(delete(models.Subscriptions))

            session.commit()
            
        except Exception as e:
            session.rollback()
            raise