-- shows where the payload will go to
CREATE TABLE subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  url TEXT NOT NULL,
  event_types text[] NOT NULL,
  secret TEXT NOT NULL,
  active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  constraint subscriptions_event_types_not_empty
    check (cardinality(event_types) > 0)
);

CREATE INDEX idx_event_types_subscriptions ON subscriptions USING GIN (event_types);

-- all the events that had happened
CREATE TABLE events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  occurred_at TIMESTAMPTZ NOT NULL
);

-- what should be sent out to the destination url and shows the status and attempt nos
CREATE TABLE deliveries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  event_id UUID REFERENCES events(id) NOT NULL,
  subscription_id UUID REFERENCES subscriptions(id) NOT NULL,
  status TEXT DEFAULT 'pending' NOT NULL,
  attempt_count INT DEFAULT 0 NOT NULL,
  next_attempt_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT deliveries_check_status
    CHECK (status IN ('pending', 'in_flight', 'succeeded', 'exhausted')),
  CONSTRAINT deliveries_check_attempts
    CHECK (attempt_count >= 0)
);

CREATE INDEX idx_event_id_deliveries ON deliveries(event_id);
CREATE INDEX idx_subscription_id_deliveries ON deliveries(subscription_id);
CREATE INDEX idx_deliveries_due ON deliveries(status, next_attempt_at);

-- delivery attempts shows the log of all deliveries made
CREATE TABLE delivery_attempts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  delivery_id UUID references deliveries(id) NOT NULL,
  attempt_no INT NOT NULL,
  status_code INT,
  response_snippet TEXT,
  error TEXT,
  duration_ms INT NOT NULL,
  attempted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  CONSTRAINT delivery_attempts_unique
    UNIQUE(delivery_id, attempt_no)
);
