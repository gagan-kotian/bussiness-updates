from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="business"
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="business"
    )

    entities: Mapped[list["Entity"]] = relationship(
        back_populates="business"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    business_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("businesses.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    business: Mapped["Business"] = relationship(
        back_populates="users"
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="sender"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    business_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("businesses.id"),
        nullable=False
    )

    sender_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    business: Mapped["Business"] = relationship(
        back_populates="messages"
    )

    sender: Mapped["User"] = relationship(
        back_populates="messages"
    )

    entity_links: Mapped[list["MessageEntity"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_messages_business_sent_at",
            "business_id",
            "sent_at"
        ),
        Index(
            "idx_messages_business_sender",
            "business_id",
            "sender_id"
        ),
    )


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    business_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("businesses.id"),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    entity_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    business: Mapped["Business"] = relationship(
        back_populates="entities"
    )

    message_links: Mapped[list["MessageEntity"]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "entity_type",
            "entity_key",
            name="uq_business_entity"
        ),
        Index(
            "idx_entities_business_type_key",
            "business_id",
            "entity_type",
            "entity_key"
        ),
    )


class MessageEntity(Base):
    __tablename__ = "message_entities"

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("messages.id"),
        primary_key=True
    )

    entity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("entities.id"),
        primary_key=True
    )

    message: Mapped["Message"] = relationship(
        back_populates="entity_links"
    )

    entity: Mapped["Entity"] = relationship(
        back_populates="message_links"
    )