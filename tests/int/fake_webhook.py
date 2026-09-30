from fastapi import FastAPI, Response

import time


app = FastAPI()

@app.post("/webhook")
def webhook():
    """
    For testing purposes and used to check when the receiver would respond with error code 2XXX
    """
    return Response(status_code=200)

attempt_count = 0
@app.post("/webhook/retry-test")
def webhook_retry():
    """
    Creates a retry func to check how the celery worker would work well when responding with POST request failures.
    In this case for the 1sst 3 tries, there will be an error, and a succesful POST request on the last try.
    """
    global attempt_count
    attempt_count += 1

    print("POST failed. retrying again")
    if attempt_count < 3:
        return Response(status_code=500)

    return Response(status_code=200)

@app.post("/webhook/all-fail")
def webhook_fail():
    """
    Always returns a failed attempt
    """
    return Response(status_code=500)

@app.post("/webhook/slow")
def webhook_slow():
    """
    Recreates a slow reponding server
    """
    time.sleep(10)
    return Response(200)