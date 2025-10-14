from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from service.database.models import TroubleshootingHistory, ServiceTicket


def save_troubleshooting_history(
    db: Session,
    door_serial: str,
    door_type: str,
    start_time: datetime,
    end_time: datetime,
    final_node: str,
    history_steps: List[Dict[str, Any]],
) -> TroubleshootingHistory:
    """
    Save a troubleshooting session to the database.

    Args:
        db: Database session
        door_serial: Door serial number
        door_type: Type of door
        start_time: Session start time
        end_time: Session end time
        final_node: Final node ID in troubleshooting tree
        history_steps: List of steps taken during troubleshooting

    Returns:
        Created TroubleshootingHistory instance
    """
    history = TroubleshootingHistory(
        door_serial=door_serial,
        door_type=door_type,
        start_time=start_time,
        end_time=end_time,
        final_node=final_node,
        history_steps=history_steps,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


def create_service_ticket(
    db: Session,
    history_id: int,
    contact_name: str,
    contact_phone: str,
    contact_email: str,
    priority: str,
    additional_info: Optional[str] = None,
) -> ServiceTicket:
    """
    Create a service ticket linked to a troubleshooting history.

    Args:
        db: Database session
        history_id: ID of the related troubleshooting history
        contact_name: Name of contact person
        contact_phone: Contact phone number
        contact_email: Contact email
        priority: Ticket priority level
        additional_info: Optional additional information

    Returns:
        Created ServiceTicket instance
    """
    ticket = ServiceTicket(
        history_id=history_id,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        priority=priority,
        additional_info=additional_info,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def create_direct_service_ticket(
    db: Session,
    door_serial: str,
    door_type: str,
    contact_name: str,
    contact_phone: str,
    contact_email: str,
    priority: str,
    additional_info: Optional[str] = None,
) -> ServiceTicket:
    """
    Create a service ticket directly without a troubleshooting history.
    Creates a minimal history record to maintain database relationships.

    Args:
        db: Database session
        door_serial: Door serial number
        door_type: Type of door
        contact_name: Name of contact person
        contact_phone: Contact phone number
        contact_email: Contact email address
        priority: Ticket priority level
        additional_info: Optional additional information

    Returns:
        Created ServiceTicket instance
    """
    # Create a minimal history record for direct tickets
    history = TroubleshootingHistory(
        door_serial=door_serial,
        door_type=door_type,
        start_time=datetime.now(pytz.timezone("Europe/Berlin")),
        end_time=datetime.now(pytz.timezone("Europe/Berlin")),
        final_node="direct_service_request",
        history_steps=[
            {
                "timestamp": datetime.now(pytz.timezone("Europe/Berlin")).isoformat(),
                "node_text": "Direktes Service-Ticket",
                "response": "✓",
            }
        ],
    )
    db.add(history)
    db.flush()  # Get the history ID

    # Create the service ticket
    ticket = ServiceTicket(
        history_id=history.id,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        priority=priority,
        additional_info=additional_info,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def get_session() -> Session:
    """
    Get a database session.
    """
    from door_service.database.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
