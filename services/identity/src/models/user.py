import uuid
from sqlalchemy import Enum as SAEnum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.domain.enums import UserStatus
from src.models.mixins import TimestampMixin


class User(TimestampMixin, Base):

    __tablename__= "users"

    id:Mapped[uuid.UUID]=mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    email:Mapped[str]=mapped_column(
        String(320),
        unique=True,
        nullable=False
    )

    phone:Mapped[str | None]=mapped_column(
        String(30),
        unique=True,
        nullable=True
    )

    display_name:Mapped[str]=mapped_column(
        String(100),
        nullable=False
    )

    status:Mapped[UserStatus]=mapped_column(
        SAEnum(
            UserStatus,
            name="user_status"
        ),
        nullable=False,
        default=UserStatus.PENDING
    )