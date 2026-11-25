"""Execução OpenCL em CPU; contexto e programa imutáveis são reutilizados."""

from functools import lru_cache
from importlib.resources import files
from threading import Lock

_initialization_lock = Lock()


@lru_cache(maxsize=1)
def _runtime():
    """Inicializa sob demanda; importar a API não exige driver ou plataforma.

    O lock externo em compare_batch impede compilações duplicadas na primeira
    chamada. Falhas não ficam em cache e podem ser recuperadas posteriormente.
    """
    import numpy as np
    import pyopencl as cl

    devices = [
        device for platform in cl.get_platforms()
        for device in platform.get_devices(device_type=cl.device_type.CPU)
    ]
    if not devices:
        raise RuntimeError("Dispositivo OpenCL CPU indisponível")
    context = cl.Context(devices=[devices[0]])
    source = files("app.appointments").joinpath("kernels/check_overlap.cl").read_text()
    program = cl.Program(context, source).build()
    return np, cl, context, program, devices[0]


def runtime_info() -> dict:
    """Disponibiliza apenas identificação técnica para testes e medições."""
    with _initialization_lock:
        np, cl, _, _, device = _runtime()
    return {
        "platform": device.platform.name, "device": device.name,
        "device_type": cl.device_type.to_string(device.type),
        "driver": device.driver_version, "opencl": device.version,
        "pyopencl": cl.VERSION_TEXT, "numpy": np.__version__,
    }


def compare_batch(candidates, requested) -> tuple[bool, int]:
    """Um work-item por intervalo; redução no host evita uma flag global com corrida."""
    with _initialization_lock:
        np, cl, context, program, device = _runtime()
    if not candidates:
        return False, 0
    data = np.asarray(candidates, dtype=np.int64)
    output = np.empty(len(candidates), dtype=np.uint8)
    if data.nbytes > device.max_mem_alloc_size or output.nbytes > device.max_mem_alloc_size:
        raise ValueError("Lote excede o limite de alocação OpenCL")
    # Cada chamada possui fila, kernel e buffers próprios. set_args nunca
    # modifica um kernel compartilhado entre requisições simultâneas.
    with cl.CommandQueue(context, properties=cl.command_queue_properties.PROFILING_ENABLE) as queue:
        flags = cl.mem_flags
        input_buffer = cl.Buffer(context, flags.READ_ONLY | flags.COPY_HOST_PTR, hostbuf=data)
        output_buffer = cl.Buffer(context, flags.WRITE_ONLY, output.nbytes)
        try:
            kernel = cl.Kernel(program, "check_overlap")
            event = kernel(
                queue, (len(candidates),), None, input_buffer,
                np.int64(requested[0]), np.int64(requested[1]), output_buffer,
            )
            cl.enqueue_copy(queue, output, output_buffer).wait()
            elapsed = event.profile.end - event.profile.start
            return bool(output.any()), elapsed
        finally:
            queue.finish()
            input_buffer.release()
            output_buffer.release()
