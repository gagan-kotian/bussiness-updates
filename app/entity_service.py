import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entity, MessageEntity


ORDER_PATTERN = re.compile(
    r"\border\s*#?\s*(\d+)\b",
    re.IGNORECASE
)

HASH_PATTERN = re.compile(
    r"(?<!\w)#(\d+)\b"
)


def extract_entities(content: str) -> list[tuple[str, str]]:
    entities = set()

    # Matches:
    # Order 4521
    # Order #4521
    order_matches = ORDER_PATTERN.findall(content)

    for order_id in order_matches:
        entities.add(("order", order_id))

    # Matches:
    # #4521
    # This is treated as an order reference for this assignment.
    hash_matches = HASH_PATTERN.findall(content)

    for order_id in hash_matches:
        entities.add(("order", order_id))

    return list(entities)


def get_or_create_entity(
    db: Session,
    business_id: int,
    entity_type: str,
    entity_key: str
) -> Entity:

    query = select(Entity).where(
        Entity.business_id == business_id,
        Entity.entity_type == entity_type,
        Entity.entity_key == entity_key
    )

    entity = db.execute(query).scalar_one_or_none()

    if entity:
        return entity

    entity = Entity(
        business_id=business_id,
        entity_type=entity_type,
        entity_key=entity_key,
        display_name=f"{entity_type} #{entity_key}"
    )

    db.add(entity)
    db.flush()

    return entity


def attach_entities_to_message(
    db: Session,
    message_id: int,
    business_id: int,
    content: str
):
    entities = extract_entities(content)

    for entity_type, entity_key in entities:

        entity = get_or_create_entity(
            db=db,
            business_id=business_id,
            entity_type=entity_type,
            entity_key=entity_key
        )

        link = MessageEntity(
            message_id=message_id,
            entity_id=entity.id
        )

        db.add(link)