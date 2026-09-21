import pytest


@pytest.fixture
def valid_https_url():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "https://example.com/path/to/resource",
            "https://example.com?key=value"]

@pytest.fixture
def valid_https_url_prod():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "https://example.com/path/to/resource",
            "https://example.com?key=value"]

@pytest.fixture
def valid_https_url_dev():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "http://localhost:8000/docs", 
            "http://127.0.0.1:8000/docs"]

@pytest.fixture
def valid_event_types():
    return ["stock.replenished", "stock.adjusted_manually","lot.expiring_soon",
            "lot.expired","lot.quarantined"]

@pytest.fixture
def invalid_https_url():
    return ["http://localhost:8000/docs", "http://127.0.0.1:8000/docs", "http://localhost:8000",
            "https//example.com?key=value", "https://api.example.com/v1/subscriptions"]

@pytest.fixture
def invalid_event_types():
    return ["stock.replenifghshed", "stock.adjustd_manually","lot.expirrnig_soon",
            "lot.expdfgired","lot.quarertined"]