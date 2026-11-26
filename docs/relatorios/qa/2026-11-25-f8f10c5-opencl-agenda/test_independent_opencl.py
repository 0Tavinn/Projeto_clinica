
"""Sondagens independentes, somente QA; nao modifica arquivos da aplicacao."""
import builtins, datetime as dt, json, random, threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from app.appointments.conflict_detection import detect_conflict, interval, sequential_overlap
from app.appointments import opencl_conflicts as mod

def emit(case, **data):
    print("QA_EVIDENCE "+json.dumps({"case":case,**data},sort_keys=True),flush=True)

def test_independent_concurrent_first_initialization():
    import pyopencl as cl
    mod._runtime.cache_clear()
    real_program=cl.Program
    calls=[]
    def program(*args,**kwargs):
        calls.append(1)
        return real_program(*args,**kwargs)
    barrier=threading.Barrier(8)
    def execute(i):
        barrier.wait(timeout=10)
        result=detect_conflict([(10,20)]*13, (15,16) if i%2 else (20,21))
        assert result.conflict is bool(i%2)
        assert result.engine=="opencl" and not result.fallback and result.kernel_ns>0
        return result.kernel_ns
    with patch.object(cl,"Program",side_effect=program):
        with ThreadPoolExecutor(max_workers=8) as pool: times=list(pool.map(execute,range(8)))
    assert len(calls)==1
    emit("concurrent_first_init",compilations=len(calls),calls=len(times),kernel_ns_min=min(times),runtime=mod.runtime_info())

def test_independent_randomized_lots_and_microsecond_boundaries():
    rng=random.Random(20261125)
    cases=0
    for count in (0,1,2,17,127,4097,65537):
        data=[]
        for _ in range(count):
            a=rng.randrange(-100000,100000)
            data.append((a,a+rng.randrange(1,100)))
        for requested in [(200000,200001),(-99999,-99998),(0,1),(12345,12346)]:
            expected=sequential_overlap(data,requested)
            r=detect_conflict(iter(data),requested,engine="auto",batch_size=127)
            assert r.conflict is expected and not r.fallback
            if count:assert r.engine=="opencl" and r.kernel_ns>0
            else:assert r.engine=="sequential" and r.batches==0 and r.kernel_ns==0
            cases+=1
    utc=dt.timezone.utc
    for start in [dt.datetime(1900,1,1,tzinfo=utc),dt.datetime(2026,12,31,23,59,59,999999,tzinfo=utc),dt.datetime(9998,1,1,tzinfo=utc)]:
        end=start+dt.timedelta(minutes=1)
        for a,expected in [(end,False),(end-dt.timedelta(microseconds=1),True),(start-dt.timedelta(minutes=1),False)]:
            got=detect_conflict([interval(start,1)],interval(a,1))
            assert got.conflict is expected and got.engine=="opencl" and not got.fallback
            cases+=1
    emit("randomized_precision",comparisons=cases,seed=20261125)

def test_independent_fallback_failure_then_later_conflict(caplog):
    actual=mod.compare_batch
    calls=[]
    def stage(batch,requested):
        calls.append(batch[0])
        if len(calls)==2: raise RuntimeError("QA-sensitive-marker")
        return actual(batch,requested)
    # Failure occurs in nonconflicting batch2; conflict is in batch3.
    with patch.object(mod,"compare_batch",side_effect=stage):
        got=detect_conflict([(0,1),(2,3),(10,20)],(15,16),batch_size=1)
    assert got.conflict and got.fallback and got.engine=="mixed" and got.batches==3
    assert len(calls)==2 and got.kernel_ns>0
    assert "QA-sensitive-marker" not in caplog.text
    emit("fallback_later_conflict",batches=got.batches,engine=got.engine,compared_opencl_batches=len(calls),conflict=got.conflict)

def test_independent_compile_build_method_failure_and_recovery():
    import pyopencl as cl
    mod._runtime.cache_clear()
    class FailedBuild:
        def build(self):raise RuntimeError("QA compile method")
    with patch.object(cl,"Program",return_value=FailedBuild()):
        got=detect_conflict([(10,20)],(15,16))
    assert got.fallback and got.conflict and got.engine=="sequential"
    recovered=detect_conflict([(10,20)],(15,16))
    assert recovered.conflict and not recovered.fallback and recovered.engine=="opencl"
    emit("compile_failure_recovery",failure_engine=got.engine,recovered_engine=recovered.engine)

def test_independent_empty_never_initializes_opencl_and_sequential_never_calls():
    with patch.object(mod,"_runtime",side_effect=AssertionError("should not initialize")):
        empty=detect_conflict([], (1,2))
        reference=detect_conflict([(1,2)], (1,2),engine="sequential")
    assert empty.batches==0 and empty.kernel_ns==0 and not empty.fallback
    assert reference.conflict and reference.engine=="sequential"
    emit("empty_and_sequential",empty_batches=empty.batches,sequential_conflict=reference.conflict)
