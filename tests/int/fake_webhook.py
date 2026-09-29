from fastapi import FastAPI, Response

import time


app = FastAPI()

@app.post("/webhook")
def webhook():
    return Response(status_code=200)

attempt_count = 0
@app.post("/webhook/retry-test")
def webhook_retry():
    global attempt_count
    attempt_count += 1

    print("POST failed. retrying again")
    if attempt_count < 3:
        return Response(status_code=500)

    return Response(status_code=200)

@app.post("/webhook/all-fail")
def webhook_fail():
    return Response(status_code=500)

@app.post("/webhook/slow")
def webhook_slow():
    time.sleep(10)
    return Response(200)