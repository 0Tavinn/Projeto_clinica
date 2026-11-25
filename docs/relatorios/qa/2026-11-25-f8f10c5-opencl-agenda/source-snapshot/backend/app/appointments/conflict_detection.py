"""Comparação de intervalos da Agenda, com alternativa sequencial segura."""

import datetime
import logging
from dataclasses import dataclass
from itertools import islice
from typing import Iterable

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def to_microseconds(value: datetime.datetime) -> int:
    """Converte UTC exatamente, inclusive datas anteriores à época Unix.

    Datas sem fuso seguem a interpretação UTC já usada na Agenda.
    Evitamos timestamp() em ponto flutuante para conservar microssegundos.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    delta = value.astimezone(datetime.timezone.utc) - _EPOCH
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def interval(start: datetime.datetime, duration_minutes: int) -> tuple[int, int]:
    """Calcula o fim como datetime antes da conversão, preservando a regra atual."""
    end = start + datetime.timedelta(minutes=duration_minutes)
    return to_microseconds(start), to_microseconds(end)


def sequential_overlap(
    candidates: Iterable[tuple[int, int]], requested: tuple[int, int]
) -> bool:
    """Intervalos semiabertos adjacentes não conflitam."""
    start, end = requested
    return any(existing_start < end and start < existing_end
               for existing_start, existing_end in candidates)


@dataclass(frozen=True)
class ConflictResult:
    """Metadados técnicos internos; nenhuma informação do paciente é incluída."""

    conflict: bool
    engine: str
    batches: int
    kernel_ns: int = 0
    fallback: bool = False


def detect_conflict(
    candidates: Iterable[tuple[int, int]],
    requested: tuple[int, int],
    *,
    engine: str | None = None,
    batch_size: int | None = None,
) -> ConflictResult:
    """Processa lotes limitados e nunca interpreta falha OpenCL como ausência de conflito."""
    settings = get_settings()
    engine = settings.APPOINTMENT_CONFLICT_ENGINE if engine is None else engine
    batch_size = settings.APPOINTMENT_CONFLICT_BATCH_SIZE if batch_size is None else batch_size
    if engine not in {"auto", "sequential"}:
        raise ValueError("Motor de comparação inválido")
    if type(batch_size) is not int or not 1 <= batch_size <= 65536:
        raise ValueError("Tamanho de lote inválido")
    iterator = iter(candidates)
    batches = kernel_ns = 0
    fallback = False
    used_opencl = False
    while batch := list(islice(iterator, batch_size)):
        batches += 1
        if engine == "auto" and not fallback:
            try:
                from app.appointments.opencl_conflicts import compare_batch
                conflict, elapsed = compare_batch(batch, requested)
                kernel_ns += elapsed
                used_opencl = True
            except Exception as error:
                # Bibliotecas, driver, compilação ou execução podem falhar.
                # O lote que falhou também passa pela referência sequencial.
                logger.warning("appointment_opencl_fallback error_type=%s", type(error).__name__)
                fallback = True
                conflict = sequential_overlap(batch, requested)
        else:
            conflict = sequential_overlap(batch, requested)
        if conflict:
            break
    else:
        conflict = False
    used_engine = "mixed" if used_opencl and fallback else ("opencl" if used_opencl else "sequential")
    return ConflictResult(
        conflict, used_engine,
        batches, kernel_ns, fallback,
    )
