from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin
from app.models.enums import Department, Gender, Role


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(20))
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    department: Mapped[Department] = mapped_column(Enum(Department), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)