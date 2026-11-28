"""Busca literal autorizada. Normalização única para CPU e OpenCL."""
import unicodedata
import numpy as np
try:
    import pyopencl as cl
except ImportError:
    cl = None
from pathlib import Path
from app.config import settings

KERNEL_PATH = Path(__file__).parent / "kernels" / "contains.cl"

def normalize(value: str) -> str:
    # NFKD + casefold, removendo marcas combinantes.
    folded = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in folded if not unicodedata.combining(c))

def sequential_search(texts: list[str], term: str) -> list[int]:
    needle = normalize(term)
    return [i for i, text in enumerate(texts) if needle in normalize(text)]

class OpenCLUnavailable(RuntimeError):
    pass

class OpenCLSearch:
    def __init__(self):
        self.ctx = None
        self.queue = None
        self.program = None
        try:
            if cl is None:
                raise OpenCLUnavailable("PyOpenCL não instalado")
            platforms = cl.get_platforms()
            devices = [d for p in platforms for d in p.get_devices()]
            if not devices:
                raise RuntimeError("Nenhum dispositivo OpenCL.")
            # CPU é a opção inicial; GPU não é selecionada automaticamente.
            cpu_devices = [d for d in devices if d.type & cl.device_type.CPU]
            device = cpu_devices[0] if cpu_devices else devices[0]
            self.ctx = cl.Context([device])
            self.queue = cl.CommandQueue(self.ctx)
            self.program = cl.Program(self.ctx, KERNEL_PATH.read_text(encoding="utf-8")).build()
            self.device_name = device.name.strip()
        except Exception as exc:
            raise OpenCLUnavailable(str(exc)) from exc

    def search(self, texts: list[str], term: str) -> list[int]:
        needle = normalize(term).encode("utf-8")
        encoded = [normalize(t).encode("utf-8") for t in texts]
        if not encoded:
            return []
        if len(needle) == 0 or len(needle) > settings.opencl_max_term_chars * 4:
            raise ValueError("Termo de busca inválido.")
        total = sum(map(len, encoded))
        if total > settings.opencl_max_text_bytes:
            raise ValueError("Lote de busca excede o limite configurado.")
        offsets = np.zeros(len(encoded) + 1, dtype=np.uint64)
        for i, item in enumerate(encoded):
            offsets[i + 1] = offsets[i] + len(item)
        blob = b"".join(encoded)
        haystack = np.frombuffer(blob, dtype=np.uint8).copy()
        needle_arr = np.frombuffer(needle, dtype=np.uint8).copy()
        result = np.zeros(len(encoded), dtype=np.uint8)
        mf = cl.mem_flags
        # Buffers e kernel são criados por requisição para isolar concorrência.
        h_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=haystack)
        o_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=offsets)
        n_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=needle_arr)
        r_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, result.nbytes)
        kernel = self.program.contains_bytes
        kernel(self.queue, (len(encoded),), None, h_buf, o_buf, np.uint64(len(encoded)),
               n_buf, np.uint64(len(needle_arr)), r_buf)
        cl.enqueue_copy(self.queue, result, r_buf).wait()
        return np.flatnonzero(result).astype(int).tolist()
