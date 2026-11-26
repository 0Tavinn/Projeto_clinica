"""Equivalência, fallback e concorrência do comparador da Agenda."""

import datetime as dt
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from app.appointments.conflict_detection import detect_conflict, interval, to_microseconds
from app.appointments.opencl_conflicts import compare_batch, runtime_info
from app.core.config import Settings

CASES = [
    ([(10, 20)], (10, 20), True),
    ([(10, 20)], (15, 25), True),
    ([(10, 20)], (12, 18), True),
    ([(10, 20)], (5, 25), True),
    ([(10, 20)], (20, 30), False),
    ([(10, 20)], (0, 10), False),
    ([(10, 20)], (30, 40), False),
    ([(10, 20)], (19, 20), True),
    ([], (10, 20), False),
]


@pytest.mark.parametrize("candidates,requested,expected", CASES)
def test_sequential(candidates, requested, expected):
    assert detect_conflict(candidates, requested, engine="sequential").conflict is expected


@pytest.fixture
def real_opencl():
    try:
        info = runtime_info()
    except Exception:
        if os.environ.get("LUMINA_REQUIRE_OPENCL") == "1":
            raise
        pytest.skip("OpenCL real não disponível neste ambiente")
    assert "CPU" in info["device_type"]
    return info


@pytest.mark.parametrize("candidates,requested,expected", CASES)
def test_real_opencl(real_opencl, candidates, requested, expected):
    result = detect_conflict(candidates, requested, engine="auto")
    assert result.conflict is expected
    assert not result.fallback
    if candidates:
        assert result.engine == "opencl"
        assert result.kernel_ns > 0


def test_datetime_precision_and_timezone(real_opencl):
    utc = dt.timezone.utc
    local = dt.timezone(dt.timedelta(hours=-3))
    start = dt.datetime(2026, 12, 1, 23, 59, 59, 999999, tzinfo=utc)
    same = start.astimezone(local)
    assert interval(start, 30) == interval(same, 30)
    assert interval(start, 30) == interval(start.replace(tzinfo=None), 30)
    assert to_microseconds(dt.datetime(1969, 12, 31, 23, 59, 59, 999999, tzinfo=utc)) == -1
    end = start + dt.timedelta(minutes=30)
    for requested, expected in [(interval(end, 1), False),
                                (interval(end-dt.timedelta(microseconds=1), 1), True),
                                (interval(start+dt.timedelta(days=1), 1), False)]:
        result = detect_conflict([interval(start, 30)], requested)
        assert result.engine == "opencl" and result.conflict is expected


@pytest.mark.parametrize("count", [1, 4096, 4097, 65539])
def test_all_batches_including_last(real_opencl, count):
    data = [(0, 1)] * count + [(10, 20)]
    result = detect_conflict(iter(data), (15, 16), batch_size=4096)
    assert result.engine == "opencl" and result.conflict
    assert result.batches == (len(data)+4095)//4096
    assert not detect_conflict(data, (30, 31)).conflict


@pytest.mark.parametrize("failure", [ImportError, RuntimeError, MemoryError])
@pytest.mark.parametrize("expected", [False, True])
def test_fallback_never_opens_slot(failure, expected):
    data = [(10, 20)] if expected else [(0, 1)]
    with patch("app.appointments.opencl_conflicts.compare_batch", side_effect=failure()):
        result = detect_conflict(data, (15, 16))
    assert result.conflict is expected and result.fallback
    assert result.engine == "sequential"


def test_error_after_successful_batch(real_opencl):
    def fail_second(data, requested):
        if data[0] == (10, 20):
            raise RuntimeError("Falha simulada")
        return compare_batch(data, requested)
    with patch("app.appointments.opencl_conflicts.compare_batch", side_effect=fail_second):
        result = detect_conflict([(0, 1), (10, 20)], (15, 16), batch_size=1)
    assert result.conflict and result.fallback and result.batches == 2
    assert result.engine == "mixed" and result.kernel_ns > 0


def test_independent_queues_and_kernels(real_opencl):
    def run(index):
        expected = bool(index % 2)
        result = detect_conflict([(10, 20)] * 65, (15, 16) if expected else (20, 21))
        assert result.engine == "opencl" and not result.fallback
        assert result.conflict is expected
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(run, range(64)))


@pytest.mark.parametrize("value", [0, -1, 65537, True, 1.5, "10"])
def test_batch_validation(value):
    with pytest.raises(ValueError):
        detect_conflict([], (0, 1), batch_size=value)


def test_settings_validation():
    with pytest.raises(ValueError):
        Settings(APPOINTMENT_CONFLICT_ENGINE="gpu")
    with pytest.raises(ValueError):
        Settings(APPOINTMENT_CONFLICT_BATCH_SIZE=0)


@pytest.mark.parametrize("stage", ["library", "platform", "device", "build", "kernel"])
@pytest.mark.parametrize("expected", [False, True])
def test_runtime_failure_stages(real_opencl, stage, expected):
    """Indisponibilidade em cada etapa nunca libera um intervalo conflitante."""
    import builtins
    import pyopencl as cl
    from app.appointments.opencl_conflicts import _runtime

    original_import = builtins.__import__
    def missing_library(name, *args, **kwargs):
        if name == "pyopencl":
            raise ImportError("Simulação controlada")
        return original_import(name, *args, **kwargs)
    replacements = {
        "library": patch("builtins.__import__", side_effect=missing_library),
        "platform": patch.object(cl, "get_platforms", side_effect=RuntimeError()),
        "device": patch.object(cl, "get_platforms", return_value=[]),
        "build": patch.object(cl, "Program", side_effect=RuntimeError()),
        "kernel": patch.object(cl, "Kernel", side_effect=RuntimeError()),
    }
    _runtime.cache_clear()
    try:
        with replacements[stage]:
            result = detect_conflict([(10, 20)] if expected else [(0, 1)], (15, 16))
        assert result.conflict is expected and result.fallback
        assert result.engine == "sequential"
    finally:
        _runtime.cache_clear()
