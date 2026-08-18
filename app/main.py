from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.entity_service import attach_entities_to_message
from app.schemas import (
    EntityMessageResponse,
    MessageCreate,
    MessageResponse,
)
from app.models import (
    Business,
    Entity,
    Message,
    MessageEntity,
    User,
)


app = FastAPI(
    title="Business Updates API",
    version="1.0.0"
)


Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {
        "message": "Business Updates API is running"
    }


@app.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    # Check business
    business = db.get(
        Business,
        message.business_id
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Check sender
    sender = db.get(
        User,
        message.sender_id
    )

    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender not found"
        )

    # Check sender belongs to business
    if sender.business_id != message.business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender does not belong to this business"
        )

    # Create message
    new_message = Message(
        business_id=message.business_id,
        sender_id=message.sender_id,
        content=message.content,
        sent_at=message.sent_at
    )

    db.add(new_message)
    db.flush()

    # Extract and attach entities
    attach_entities_to_message(
        db=db,
        message_id=new_message.id,
        business_id=message.business_id,
        content=message.content
    )

    db.commit()
    db.refresh(new_message)

    return new_message


@app.get(
    "/messages",
    response_model=list[MessageResponse]
)
def get_messages(
    business_id: int,
    sender_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    keyword: str | None = Query(
        default=None,
        min_length=1
    ),
    db: Session = Depends(get_db)
):
    query = select(Message).where(
        Message.business_id == business_id
    )

    if sender_id is not None:
        query = query.where(
            Message.sender_id == sender_id
        )

    if from_date is not None:
        query = query.where(
            Message.sent_at >= from_date
        )

    if to_date is not None:
        query = query.where(
            Message.sent_at <= to_date
        )

    if keyword is not None:
        query = query.where(
            Message.content.ilike(
                f"%{keyword}%"
            )
        )

    query = query.order_by(
        Message.sent_at.desc()
    )

    result = db.execute(query)

    return result.scalars().all()


@app.get(
    "/entities/{entity_type}/{entity_key}/messages",
    response_model=list[EntityMessageResponse]
)
def get_entity_messages(
    entity_type: str,
    entity_key: str,
    business_id: int,
    db: Session = Depends(get_db)
):
    # Find the entity belonging to this business
    entity_query = select(Entity).where(
        Entity.business_id == business_id,
        Entity.entity_type == entity_type.lower(),
        Entity.entity_key == entity_key
    )

    entity = db.execute(
        entity_query
    ).scalar_one_or_none()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found"
        )

    # Find all messages connected to this entity
    message_query = (
        select(Message)
        .join(
            MessageEntity,
            Message.id == MessageEntity.message_id
        )
        .where(
            MessageEntity.entity_id == entity.id,
            Message.business_id == business_id
        )
        .order_by(Message.sent_at.asc())
    )

    result = db.execute(message_query)

    return result.scalars().all()