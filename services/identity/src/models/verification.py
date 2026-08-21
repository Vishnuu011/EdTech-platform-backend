import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.domain.enums import (
    VerificationStatus,
    VerificationType,
)


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[VerificationType] = mapped_column(
        SAEnum(
            VerificationType,
            name="verification_type",
        ),
        nullable=False,
    )

    destination: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    code_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="verification_status",
        ),
        nullable=False,
        default=VerificationStatus.PENDING,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "attempts >= 0",
            name="ck_verification_attempts_non_negative",
        ),
        CheckConstraint(
            "max_attempts > 0",
            name="ck_verification_max_attempts_positive",
        ),
        CheckConstraint(
            "attempts <= max_attempts",
            name="ck_verification_attempts_limit",
        ),
    )