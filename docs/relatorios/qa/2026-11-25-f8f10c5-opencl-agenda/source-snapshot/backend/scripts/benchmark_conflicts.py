"""Medição educativa com dados fictícios; exclui SQL, HTTP e rede."""

import json
import time
from statistics import median

from app.appointments.conflict_detection import detect_conflict
from app.appointments.opencl_conflicts import runtime_info


def main():
    """Mede inicialização separadamente e o custo completo do comparador por lote."""
    start = time.perf_counter_ns()
    info = runtime_info()
    initialization = time.perf_counter_ns() - start
    rows = []
    for count in (0, 32, 4096, 65536):
        candidates = [(index * 60, index * 60 + 30) for index in range(count)]
        requested = (-60, -30)
        for engine in ("sequential", "auto"):
            elapsed, kernels = [], []
            for _ in range(5):
                start = time.perf_counter_ns()
                result = detect_conflict(candidates, requested, engine=engine)
                elapsed.append(time.perf_counter_ns() - start)
                kernels.append(result.kernel_ns)
                assert not result.conflict and not result.fallback
                if count and engine == "auto":
                    assert result.engine == "opencl"
            rows.append({
                "count": count, "requested_engine": engine, "engine": result.engine,
                "batch_size": 4096, "total_median_ns": median(elapsed),
                "kernel_median_ns": median(kernels), "repetitions": 5,
            })
    print(json.dumps({"runtime": info, "initialization_ns": initialization,
                      "scope": "comparador; exclui SQL/HTTP/rede; cache do driver pode existir",
                      "measurements": rows}, indent=2))


if __name__ == "__main__":
    main()
