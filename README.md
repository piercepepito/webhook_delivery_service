# Webhook Delivery Service

Infrastructure that turns a business event into a **signed HTTP notification** delivered to every
subscriber who registered. Retrying on failure and recording every attempt so delivery is
observable.

---

## The problem it solves

Without this service, a producer that wants to notify consumers has to hold their URLs, know their
retry policies, sign its own requests, and track what succeeded. Adding a consumer means editing and
redeploying the producer. On top of the infrastructure the producer is making, the sending itself would 
make it very cumbersome on there part.

by using this, the producer makes **one call** and doesn't have to think about the other requirements needed to send to a customer.

| | Without the service | With the service |
|---|---|---|
| Consumer URLs live in | The producer's code | A database row |
| Adding a consumer | Edit + redeploy | `INSERT` |
| Retry logic | The producer's problem | The worker's |
| Signing | The producer's problem | The worker's |
| "Did it arrive?" | Nobody knows | The delivery log answers |

---

## Features

### Subscription management

- Create a subscription with a destination URL and the event types it wants to receive
- Retrieve a subscription by id, and partially update it with `PATCH` without resending unchanged fields
- A per-subscription HMAC signing secret, generated server-side and returned exactly once
- Fan-out filters on `active`, so a disabled subscriber stops receiving deliveries without losing its history

### Event ingest and fan-out

- A **closed event catalog** validated at the API boundary — unknown types are rejected with `422` rather than silently matching nothing
- Fan-out matches on event type, then creates one delivery row per match
- An event with no matching subscribers produces zero deliveries.
- `occurred_at` is recorded separately from `created_at`, so ingestion lag is measurable
- `POST /v1/events` reports the fan-out result per delivery: delivery id, subscription id, task id

### Delivery

- A dedicated Celery worker performs the outbound HTTP.
- **HMAC-SHA256** signature on every request via `X-Webhook-Signature`
- **Exponential backoff** retries: 5s → 10s → 20s → 40s → 80s, capped at 5 retries
- Explicit `timeout=(3, 5)` on outbound calls, so one slow receiver cannot occupy a worker indefinitely
- `exhausted` is a recorded terminal state, not a discarded error. This only shows when retries have already been exhausted.
- Manual re-attempt of a failed delivery via `POST /v1/deliveries/retry/{id}`, refusing with `406` if it already succeeded. This is used in case something in the server of the subscriber may have failed.

### Security

- Signing secrets **encrypted** with Fernet (authenticated encryption), decrypted only in the worker immediately before signing
- The encryption key is held outside the database — encrypting with a key stored beside the data would protect nothing
- Secrets returned once at creation and **excluded from every read response**, enforced by response models rather than by discipline
- HTTPS-only destination URLs, with a development-only allowance for `localhost` and `127.0.0.1`

### Observability

- Every outbound call is logged to `delivery_attempts`: status code, truncated response body, error, duration
- `status_code` is nullable, making *"the receiver returned an error"* distinguishable from *"we never reached them"*
- Delivery status, attempt count and retry schedule are all queryable through the API

### Data integrity

- The event and all of its deliveries are written in **one transaction** — an orphaned event cannot exist
- `delivery_attempts` is append-only with `UNIQUE (delivery_id, attempt_no)`, so a retried write cannot duplicate a row
- Events are immutable and append-only — facts about the past, never updated
- Subscriptions are deactivated rather than deleted, preserving referential history

---

## Architecture

Two independent processes that never call each other directly — they communicate only through Redis.

```
┌──────────────────┐        ┌─────────────┐        ┌──────────────────┐
│  Producer        │──POST──▶   FastAPI     │        │  Celery worker   │
│  (warehouse app) │        │  (uvicorn)   │        │  (no HTTP port)  │
└──────────────────┘        └──────┬───────┘        └────────┬─────────┘
                                   │                          │
                              writes/reads               writes/reads
                                   │                          │
                            ┌──────▼───────┐          ┌───────▼────────┐
                            │  PostgreSQL  │          │     Redis      │
                            │  (state)     │          │  (broker)      │
                            └──────────────┘          └───────┬────────┘
                                                              │ task
                                   ┌──────────────────────────▼─────────┐
                                   │  Subscriber endpoint (outbound POST)│
                                   └────────────────────────────────────┘
```

| Component | Process | Role |
|---|---|---|
| `main.py` + `routers/` | FastAPI / uvicorn | HTTP API — subscriptions, event ingest, fan-out, enqueue |
| `worker/` | Celery | Outbound delivery, signing, retries |
| PostgreSQL | — | Durable state: events, deliveries, attempts |
| Redis | — | Celery broker and result backend |

### Why the split matters

The API responds without waiting on any outbound HTTP call. A subscriber being down for
an hour does not slow the API, block other subscribers, or cause a lost event. The work waits in the
queue and the delivery row holds the state.

---

## How an event flows

**Inside the HTTP request:**

1. `POST /v1/events` validates the event type against the catalog
2. The event row is inserted into `events`
3. `subscriptions.get_subscription_url(type)` selects subscriptions whose `event_types` contain that
   type
4. One `deliveries` row is created per matching subscription
5. One Celery task is enqueued per delivery
6. `201 Created` is returned — the producer is done

**Later, in the worker (asynchronous):**

7. The worker picks up a task
8. The signing secret is **decrypted** from the database
9. An HMAC-SHA256 signature is computed over the JSON body
10. The webhook is POSTed to the subscriber's URL
11. A `delivery_attempts` row records the outcome
12. The `deliveries` row is updated — succeeded, or rescheduled for a retry

The HTTP response at step 6 means **"recorded," not "delivered."** An event with zero matching
subscriptions returns 201 and produces zero deliveries.

---

## API reference

| Method | Path | Status | Response model | Purpose |
|---|---|---|---|---|
| `POST` | `/v1/subscriptions` | 201 | `SubscriptionCreated` | Create a subscription; returns the signing secret **once** |
| `GET` | `/v1/subscriptions/{id}` | 200 | `SubscriptionRead` | Fetch one subscription (never includes the secret) |
| `PATCH` | `/v1/subscriptions/{id}` | 200 | `SubscriptionRead` | Partial update — `url` and/or `event_types` |
| `POST` | `/v1/events` | 201 | `list[FanOutSent]` | Creaetes an event and fan out |
| `GET` | `/v1/deliveries/{id}` | 200 | `DeliveryGet` | Delivery status — the visibility endpoint |
| `POST` | `/v1/deliveries/retry/{id}` | 200 | `RetryDelivery` | Manually re-attempt a delivery |

### `POST /v1/subscriptions`

```json
{
  "url": "https://northgate.example.com/hooks/warehouse",
  "event_types": ["stock.below_reorder_point", "stock.replenished"]
}
```

Validation rules:

- `url` must be `https` — except `http://localhost` and `http://127.0.0.1` when `ENVIRONMENT=development`
- `event_types` may not be empty, and every value must exist in the event catalog

Returns `201` with the created subscription **including its unencrypted secret**. This is the only moment the
secret key is ever available. It is encrypted when stored in the database, excluded from every read response. Lose it and the subscription is unusable.

### `PATCH /v1/subscriptions/{id}`

```json
{ "event_types": ["asset.serial_registered"] }
```

Both fields are optional, but at least one must be present. Omitted fields are left unchanged.
Subscriptions are **deactivated, never deleted**. A foreign key reveals from deliveries, shows that they are being referenced.

### `POST /v1/events`

```json
{
  "type": "stock.below_reorder_point",
  "occurred_at": "2026-09-18T09:14:22+08:00",
  "payload": {
    "sku": "FLOUR-BREAD-25KG",
    "current_qty": 38,
    "reorder_point": 40
  }
}
```

`type` must be in the catalog. `occurred_at` must be timezone-aware. Returns one `FanOutSent` entry per
matching subscription.

---

## Data model

```
subscriptions ──┐
                ├──< deliveries ──< delivery_attempts
events ─────────┘
```

**`subscriptions`** — a standing registration: who wants which events, sent where.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | `gen_random_uuid()` |
| `url` | TEXT | Destination endpoint |
| `event_types` | TEXT[] | GIN-indexed; `CHECK (cardinality > 0)` |
| `secret` | TEXT | HMAC signing secret, **encrypted at rest** |
| `active` | BOOLEAN | Filters fan-out |
| `created_at` | TIMESTAMPTZ | |

**`events`** — immutable, append-only record of something that happened.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `type` | TEXT | From the catalog |
| `payload` | JSONB | Opaque to this service — never inspected |
| `created_at` | TIMESTAMPTZ | When **we received** it |
| `occurred_at` | TIMESTAMPTZ | When it **actually happened** |

**`deliveries`** — one row per (event × subscription). 

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `event_id` | UUID FK | |
| `subscription_id` | UUID FK | |
| `status` | TEXT | `pending` / `in_flight` / `succeeded` / `exhausted` |
| `attempt_count` | INT | |
| `next_attempt_at` | TIMESTAMPTZ | Drives the retry schedule |
| `created_at` | TIMESTAMPTZ | |

**`delivery_attempts`** — append-only log, one row per HTTP call actually made.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `delivery_id` | UUID FK | `UNIQUE (delivery_id, attempt_no)` |
| `attempt_no` | INT | 1-based |
| `status_code` | INT | **NULL** if the request never completed |
| `response_snippet` | TEXT | Truncated receiver response |
| `error` | TEXT | Connection / timeout detail |
| `duration_ms` | INT | |
| `attempted_at` | TIMESTAMPTZ | |

`status_code` is nullable by design: a refused connection has no HTTP status, and inventing `0` would be
indistinguishable from a real one.

Splitting `deliveries` (mutable job state) from `delivery_attempts` (immutable history) is what makes the
retry and audit story possible: one delivery, many attempts.

---

## Delivery lifecycle and retries

```
pending ──▶ in_flight ──▶ succeeded
                │
                ├──▶ in_flight  (retry scheduled; attempt_count < max)
                └──▶ exhausted  (max attempts reached)
```

### Exponential backoff

Retries are handled by Celery's own retry mechanism, using **exponential backoff** — the delay **doubles**
on every attempt:

| Attempt | Delay before it |
|---|---|
| 1 | immediate |
| 2 | 5s |
| 3 | 10s |
| 4 | 20s |
| 5 | 40s |
| 6 | 80s |
| — | then `exhausted` |

`wait = 5 * 2 ** retries`, capped at `max_retries = 5`.

The doubling is the point. A receiver that is down for an hour gets retried at 5s, 10s, 20s, 40s. This is to ensure that 
the retries themselves are not the ones causing the outage.

`POST /v1/deliveries/retry/{id}` re-attempts synchronously. It refuses with `406` if the delivery already
succeeded. A manual retry does not schedule further retries: the outcome is `succeeded` or `exhausted`.

---

## Security

### Secrets encrypted at rest

Every subscription's signing secret is generated server-side with `secrets.token_urlsafe(32)` and
encrypted with **Fernet** before it touches the database.

- The encryption key lives in `ENCRYPTION_KEY`, **never in the database**. Otherwise encrypting would
  protect nothing
- The worker decrypts immediately before signing, and nowhere else
- This protects against a leaked database dump, a backup, or secrets captured in logs. It does **not**
  protect against someone with access to the `.env` file

Since the secret must be used whenever a delivery is being done, hashing would be a wrong application here. 
It must be recoverable, which is encryption was used for this application.

### HMAC signatures

Every outbound webhook carries:

```
X-Webhook-Signature: <hex hmac_sha256(secret, json_body)>
Content-Type: application/json
```

A receiver verifies by recomputing the HMAC with the secret it stored at subscription time and comparing
in constant time:

```python
import hmac, hashlib, json

def verify(secret: str, raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

Use `hmac.compare_digest`, never `==` — string comparison short-circuits and leaks timing information.

HMAC provides **authenticity and integrity**, not confidentiality. It proves the payload came from
someone holding the secret and was not altered in transit. It does not hide the payload; that is TLS's
job, which is why subscriber URLs must be HTTPS.

---

## Event catalog

`event_catalog.py` defines a **closed set** of event types. Subscribers may only subscribe to these and
producers may only publish these — anything else is rejected with `422` at the API boundary.

```
stock.below_reorder_point    stock.replenished       stock.adjusted_manually
lot.expiring_soon            lot.expired             lot.quarantined
receipt.completed            receipt.mismatch_detected
shipment.dispatched          shipment.delivered      shipment.delayed
asset.serial_registered      asset.decommissioned
```

The catalog is a closed set on purpose. If arbitrary strings were accepted, a subscriber typo
(`stock.below_reorderpoint`) would validate, store, and then **silently never match anything** — no
delivery, no error, no way to notice. Rejecting at the boundary turns a silent failure into a 422 that
names the offending value.

---

## Configuration

Copy the template and fill in real values. `.env` is gitignored; `.env.example` is committed and holds
no real credentials:

```bash
cp .env.example .env
```

Then set:

```
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:5432/<db>
ENCRYPTION_KEY=<44-character urlsafe base64 Fernet key>
ENVIRONMENT=development
```

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string. Use `postgresql+psycopg://` — psycopg 3, not psycopg2 |
| `ENCRYPTION_KEY` | Fernet key for secret encryption |
| `ENVIRONMENT` | `development` permits `http://localhost` and `http://127.0.0.1` as subscription URLs. Anything else requires HTTPS |
| `REDIS_URL` | Celery broker and result backend. **Not read by the code yet** — `worker/celery_app.py` currently hardcodes `redis://localhost:6379/0` |

Generate the encryption key **once, by hand**:

```bash
python -m encryption.key_generation
```

Paste the output into `.env`. Do not generate it at application startup — a new key on every restart would
make every stored secret permanently undecryptable.

---

## Getting started

**Prerequisites:** Python 3.13, a PostgreSQL database, Redis running locally.

```bash
# 1. Environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure — create .env with DATABASE_URL and ENCRYPTION_KEY (see above)

# 3. Schema — run the migrations in order against your database
#    migrations/001_init.sql
#    migrations/002_attempt_count_cleanup.sql

# 4. API (terminal 1)
uvicorn main:app --reload

# 5. Worker (terminal 2)
celery -A worker.celery_app worker --loglevel=info
```

The API is at `http://127.0.0.1:8000`, with interactive docs at `/docs`.

Redis is expected at `redis://localhost:6379/0` (configured in `worker/celery_app.py`).

---

## Docker

The `Dockerfile` builds a **single image used by both processes**. The API and the worker are the same
codebase; they differ only in the command they start with.

```bash
docker build -t webhook-delivery-service:local .
```

### What goes into the image

| Included | Excluded, via `.dockerignore` |
|---|---|
| A `python:3.13-slim` base | `.venv/` — platform-specific and hundreds of MB |
| Source code | **`.env` — secrets must never reach an image layer** |
| Everything in `requirements.txt` | `.git/`, `__pycache__/`, `.pytest_cache/` |

### Running the API

```bash
docker run --rm -p 8000:8000 --env-file .env webhook-delivery-service:local
```

The image's default command is uvicorn, so this starts the API. `--env-file .env` supplies
`DATABASE_URL` and `ENCRYPTION_KEY` at runtime, from the host, without either entering the image.

### Running the worker

The same image with a different command — this pairing is the whole reason one build serves two
processes:

```bash
docker run --rm --env-file .env webhook-delivery-service:local \
  celery -A worker.celery_app worker --loglevel=info
```

Everything after the image name **replaces** the Dockerfile's `CMD`.

> The worker needs a reachable Redis broker over a shared network. `worker/celery_app.py` currently
> hardcodes `redis://localhost:6379/0`, which inside a container points at the container itself — so
> this command will not connect until that value becomes configurable.

### Four details worth knowing

**`--host 0.0.0.0` in the CMD.** Uvicorn binds to `127.0.0.1` by default, which inside a container
means *reachable only from inside this container*. The API would start cleanly and be completely
unreachable from the host.

**Exec form (`["uvicorn", ...]`), not a shell string.** Shell form makes `/bin/sh` PID 1, so SIGTERM
goes to the shell and never reaches uvicorn — `docker stop` then waits out its timeout and force-kills
the process instead of shutting it down cleanly.

**Non-root by default.** The image creates `appuser` (uid 1000), switches to it, and copies source with
`--chown` so ownership is correct as files land. Running as root is a standard security finding.

**No `apt-get` at all.** psycopg 3, cryptography and cffi all resolve to prebuilt manylinux wheels, so
there is nothing to compile. The resulting image is around 305 MB.

---

## Testing

```bash
pytest                          # everything
pytest -m "not integration"     # unit tests only — no database required
pytest tests/unit               # the fast suite
```

| Directory | Kind | Needs a database? |
|---|---|---|
| `tests/unit/` | Pure logic — signature generation, validation, mocked webhook calls | ❌ |
| `tests/int/` | Integration — real database, fan-out, deliveries, tasks | ✅ |

The split is deliberate: the unit suite runs in milliseconds with no infrastructure, so it stays runnable
when the database is unavailable. `pythonpath=.` in `pytest.ini` puts the project root on `sys.path` so
tests can import application modules regardless of the working directory.

A Celery worker must be running for tests that assert on task execution.

---

## Project layout

```
webhook_delivery_service/
├── Dockerfile               Builds the image both processes run
├── .dockerignore            What is kept out of the build context
├── .env.example             Template for the runtime environment
├── main.py                  FastAPI app and all routes
├── db.py                    Engine, session factory, declarative Base
├── models.py                SQLAlchemy models — four tables
├── event_catalog.py         The closed set of event types
├── routers/                 HTTP handlers + the functions they call
│   ├── subscriptions.py       create / get / update / fan-out matching
│   ├── events.py              event persistence
│   ├── deliveries.py          delivery create, get, patch
│   ├── delivery_attempts.py   attempt log writes
│   └── exceptions.py          domain exceptions
├── schemas/                 Pydantic request/response models
├── database/                Multi-table operations
├── worker/                  Everything the Celery worker runs
│   ├── celery_app.py          Celery instance and broker config
│   ├── tasks.py               fan_out, delivery, retry_delivery
│   ├── webhook.py             decrypt → sign → POST
│   └── exceptions.py          WebDeliveryError
├── encryption/              Fernet secret encryption
│   ├── encryption.py          encrypt_keys / decrypt_keys
│   └── key_generation.py      One-off key generator
├── utils/
│   └── webhook_signature.py   HMAC-SHA256 signing
├── migrations/              Numbered SQL migrations
├── tests/                   unit/ and int/
└── pytest.ini
```

`db.py`, `models.py`, `event_catalog.py`, `schemas/`, `encryption/` and `utils/` sit at the root because
**both processes import them**. `routers/` belongs to the API process; `worker/` belongs to the worker
process. The layout mirrors the process boundary.

---

## Not yet implemented

Deliberately deferred — listed so the gaps are visible rather than assumed:

- **List endpoints** — `GET /v1/subscriptions` and `GET /v1/deliveries`. Today a client that loses an id
  can only recover it from the create response
- **Deactivating a subscription** — the `active` column filters fan-out, but `SubscriptionUpdate` has no
  `active` field, so nothing in the API can set it. Disabling a subscriber currently requires a direct
  database update
- **A retry sweeper** — retries currently rely on Celery's broker-side countdown. Moving `next_attempt_at`
  into a periodic poller would make retries survive a broker flush, and is what makes
  `deliveries.next_attempt_at` load-bearing
- **Jitter on the backoff** — delays are deterministic, so deliveries that fail together retry together.
  Randomising each delay by ±20% would spread the load and prevent a synchronized retry storm after an
  outage
- **Timestamped signatures** — the signature covers only the body, so a receiver cannot reject replayed
  requests by age. Signing `timestamp + "." + body` would enable a replay window
- **Authentication and tenancy** — there is no auth, and `GET /v1/deliveries/{id}` is unscoped. Every
  endpoint is effectively single-tenant
- **SSRF protection** — subscriber URLs are not checked against private, loopback or link-local ranges,
  and redirects are not disabled. Currently only the `https` scheme is enforced
- **Secret rotation** — one active secret per subscription
- **Rate limiting and payload size caps**
- **Automatic subscription disabling** after N consecutive failures

---

## Design notes

A few decisions that are non-obvious from the code:

**Postgres is written before Redis.** The event and its deliveries are committed, then tasks are enqueued.
If the process dies in between, the rows exist and the work is recoverable. Reversed, a crash would leave
a queued task pointing at a row that was never written.

**Event and delivery creation share a transaction.** Either the event and all its deliveries exist, or
none of them do.

**Subscriptions are deactivated, not deleted.** A foreign key means history references them; deleting
would create errors under the deliveries, and delivery attempt table.
