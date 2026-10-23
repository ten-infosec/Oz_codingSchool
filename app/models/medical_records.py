from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin


class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    chart_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)