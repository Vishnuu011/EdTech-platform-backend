import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.domain.enums import CredentialStatus
from src.models.mixins import TimestampMixin


class Credential(TimestampMixin, Base):
    __tablename__ = "credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[CredentialStatus] = mapped_column(
        SAEnum(
            CredentialStatus,
            name="credential_status",
        ),
        nullable=False,
        default=CredentialStatus.ACTIVE,
    )

    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )