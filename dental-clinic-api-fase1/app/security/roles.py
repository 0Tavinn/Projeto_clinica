"""
Perfis (roles) da aplicação.

Os 4 perfis do domínio completo são modelados desde já, mesmo que o MVP
ative endpoints apenas para RECEPTIONIST e DENTIST. Isso evita retrabalho de
schema/migração quando PATIENT e ADMIN forem habilitados na fase 2.
"""
import enum


class Role(str, enum.Enum):
    RECEPTIONIST = "receptionist"
    DENTIST = "dentist"
    PATIENT = "patient"  # Modelado para fase 2 — endpoints ainda não expostos.
    ADMIN = "admin"  # Modelado para fase 2 — endpoints ainda não expostos.


# Perfis com endpoints ativos no MVP atual. Usado por dependências de
# permissão para recusar, de forma explícita e auditável, qualquer uso de
# perfis ainda não habilitados — em vez de deixá-los "funcionar por acaso".
MVP_ACTIVE_ROLES: frozenset[Role] = frozenset({Role.RECEPTIONIST, Role.DENTIST})
