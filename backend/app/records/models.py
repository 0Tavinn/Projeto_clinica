import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MedicalRecord(Base):
    """Mapeia a tabela `medical_records` do PostgreSQL."""
    
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("patients.id", ondelete="RESTRICT"), 
        unique=True, 
        nullable=False
    )
    opened_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    general_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_record")
    evolutions: Mapped[list["ClinicalEvolution"]] = relationship(
        "ClinicalEvolution", back_populates="medical_record", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MedicalRecord id={self.id} patient_id={self.patient_id}>"


class ClinicalEvolution(Base):
    """Mapeia a tabela `clinical_evolutions` do PostgreSQL."""
    
    __tablename__ = "clinical_evolutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medical_record_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("medical_records.id", ondelete="RESTRICT"), 
        nullable=False
    )
    dentist_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("dentists.id", ondelete="RESTRICT"), 
        nullable=False
    )
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("appointments.id", ondelete="RESTRICT"), 
        unique=True, 
        nullable=True
    )
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT"
    )  # DRAFT ou FINALIZED
    description: Mapped[str] = mapped_column(Text, nullable=False)
    procedure_performed: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    finalized_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    medical_record: Mapped["MedicalRecord"] = relationship("MedicalRecord", back_populates="evolutions")
    dentist: Mapped["Dentist"] = relationship("Dentist") 
    
    # Descomente assim que o modelo Appointment for criado
    # appointment: Mapped["Appointment" | None] = relationship("Appointment")

    def __repr__(self) -> str:
        return f"<ClinicalEvolution id={self.id} status={self.status} dentist_id={self.dentist_id}>"