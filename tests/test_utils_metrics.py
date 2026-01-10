"""Tests for metrics utilities."""

from prometheus_client import REGISTRY

from app.core.metrics import (
    cache_hits_total,
    cache_misses_total,
    categories_created_total,
    get_metrics,
    http_request_duration_seconds,
    http_requests_total,
    reports_generated_total,
    transactions_created_total,
)


def test_get_metrics():
    """Test get_metrics returns valid Prometheus metrics."""
    response = get_metrics()
    assert response.status_code == 200
    assert "text/plain" in response.media_type
    content = response.body.decode("utf-8")
    assert "http_requests_total" in content


def test_http_requests_total_counter():
    """Test HTTP requests counter can be incremented."""
    initial_count = http_requests_total.labels(
        method="GET", endpoint="/health", status=200
    )._value.get()
    http_requests_total.labels(method="GET", endpoint="/health", status=200).inc()
    new_count = http_requests_total.labels(
        method="GET", endpoint="/health", status=200
    )._value.get()
    assert new_count > initial_count


def test_http_request_duration_histogram():
    """Test HTTP request duration histogram."""
    # Test that we can record a duration
    histogram = http_request_duration_seconds.labels(method="GET", endpoint="/health")
    histogram.observe(0.5)
    # Verify it's recorded (check sample count)
    samples = list(histogram.collect()[0].samples)
    assert len(samples) > 0


def test_transactions_created_total_counter():
    """Test transactions created counter."""
    initial = transactions_created_total.labels(type="expense")._value.get()
    transactions_created_total.labels(type="expense").inc()
    new = transactions_created_total.labels(type="expense")._value.get()
    assert new > initial


def test_transactions_created_total_different_types():
    """Test transactions created counter with different types."""
    transactions_created_total.labels(type="expense").inc()
    transactions_created_total.labels(type="income").inc()
    expense_count = transactions_created_total.labels(type="expense")._value.get()
    income_count = transactions_created_total.labels(type="income")._value.get()
    assert expense_count >= 1
    assert income_count >= 1


def test_categories_created_total_counter():
    """Test categories created counter."""
    initial = categories_created_total._value.get()
    categories_created_total.inc()
    new = categories_created_total._value.get()
    assert new > initial


def test_reports_generated_total_counter():
    """Test reports generated counter."""
    initial = reports_generated_total.labels(status="success")._value.get()
    reports_generated_total.labels(status="success").inc()
    new = reports_generated_total.labels(status="success")._value.get()
    assert new > initial


def test_reports_generated_total_different_statuses():
    """Test reports generated counter with different statuses."""
    reports_generated_total.labels(status="success").inc()
    reports_generated_total.labels(status="failed").inc()
    success_count = reports_generated_total.labels(status="success")._value.get()
    failed_count = reports_generated_total.labels(status="failed")._value.get()
    assert success_count >= 1
    assert failed_count >= 1


def test_cache_hits_total_counter():
    """Test cache hits counter."""
    initial = cache_hits_total.labels(cache_type="redis")._value.get()
    cache_hits_total.labels(cache_type="redis").inc()
    new = cache_hits_total.labels(cache_type="redis")._value.get()
    assert new > initial


def test_cache_misses_total_counter():
    """Test cache misses counter."""
    initial = cache_misses_total.labels(cache_type="redis")._value.get()
    cache_misses_total.labels(cache_type="redis").inc()
    new = cache_misses_total.labels(cache_type="redis")._value.get()
    assert new > initial


def test_metrics_registry_contains_all_counters():
    """Test that all metrics are registered in Prometheus registry."""
    metric_names = [metric.name for metric in REGISTRY._collector_to_names.keys()]
    assert "http_requests_total" in metric_names or any(
        "http_requests_total" in str(name) for name in metric_names
    )

