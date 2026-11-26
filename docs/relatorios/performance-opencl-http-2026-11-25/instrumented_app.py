"""Instrumentação exclusiva do ensaio; importa o aplicativo instalado sem editar sua fonte."""

import contextvars
import json
import time
from functools import wraps

from sqlalchemy import event
from app.main import app
from app.core.database import engine
from app.appointments import repository, opencl_conflicts

metrics = contextvars.ContextVar("perf_metrics", default=None)
original_detect = repository.detect_conflict
original_interval = repository.interval
original_runtime = opencl_conflicts._runtime
original_compare = opencl_conflicts.compare_batch


def add(name, elapsed):
    """O dicionário da requisição acompanha a execução síncrona do FastAPI."""
    current = metrics.get()
    if current is not None:
        current[name] = current.get(name, 0) + elapsed


def timed(function, label):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return function(*args, **kwargs)
        finally:
            add(label, time.perf_counter_ns()-start)
    return wrapper


def detect(*args, **kwargs):
    start = time.perf_counter_ns()
    result = original_detect(*args, **kwargs)
    add("detect_ns", time.perf_counter_ns()-start)
    current = metrics.get()
    if current is not None:
        current.update(engine=result.engine, fallback=result.fallback,
                       batches=result.batches, kernel_ns=result.kernel_ns)
    return result


class MeasuredLock:
    """Mede espera do lock de inicialização sem mudar a ordem de aquisição."""
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        start = time.perf_counter_ns()
        self.lock.acquire()
        add("runtime_lock_wait_ns", time.perf_counter_ns()-start)
        self.start = time.perf_counter_ns()
    def __exit__(self, *args):
        add("runtime_lock_hold_ns", time.perf_counter_ns()-self.start)
        self.lock.release()


def runtime():
    """Conserva o cache original; cronometra imports/contexto/build juntos."""
    start = time.perf_counter_ns()
    result = original_runtime()
    add("runtime_ns", time.perf_counter_ns()-start)
    np, cl, _, _, _ = result
    if not getattr(np.asarray, "_perf_wrapped", False):
        wrapped = timed(np.asarray, "array_prepare_ns")
        wrapped._perf_wrapped = True
        np.asarray = wrapped
    if not getattr(cl.enqueue_copy, "_perf_wrapped", False):
        copy = cl.enqueue_copy
        class ReadEvent:
            def __init__(self, event, start):
                self.event, self.start = event, start
            def wait(self):
                try:
                    return self.event.wait()
                finally:
                    add("read_enqueue_wait_ns", time.perf_counter_ns()-self.start)
        def measured_copy(*args, **kwargs):
            start = time.perf_counter_ns()
            return ReadEvent(copy(*args, **kwargs), start)
        measured_copy._perf_wrapped = True
        cl.enqueue_copy = measured_copy
    return result


@event.listens_for(engine, "before_cursor_execute")
def before_query(connection, cursor, statement, parameters, context, executemany):
    context.perf_start = time.perf_counter_ns()


@event.listens_for(engine, "after_cursor_execute")
def after_query(connection, cursor, statement, parameters, context, executemany):
    add("sql_execute_ns", time.perf_counter_ns()-context.perf_start)
    add("sql_calls", 1)


repository.detect_conflict = detect
repository.interval = timed(original_interval, "datetime_normalize_ns")
repository.AppointmentRepository.has_conflict = timed(
    repository.AppointmentRepository.has_conflict, "repository_conflict_ns")
opencl_conflicts._initialization_lock = MeasuredLock(opencl_conflicts._initialization_lock)
opencl_conflicts._runtime = runtime
opencl_conflicts.compare_batch = timed(original_compare, "opencl_host_total_ns")


@app.middleware("http")
async def measurement(request, call_next):
    """Registra só IDs de amostras, tempos e status; nunca corpos ou tokens."""
    if not request.url.path.startswith("/api/v1/appointments"):
        return await call_next(request)
    data = {"sample": request.headers.get("x-perf-case", "concurrent")}
    token = metrics.set(data)
    start = time.perf_counter_ns()
    try:
        response = await call_next(request)
        data["status"] = response.status_code
        return response
    finally:
        data["server_ns"] = time.perf_counter_ns()-start
        print("PERF "+json.dumps(data), flush=True)
        metrics.reset(token)
