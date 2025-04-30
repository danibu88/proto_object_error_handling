from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from typing import Dict, Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

Base = declarative_base()


class TroubleshootingHistory(Base):
    __tablename__ = "troubleshooting_histories"

    id = Column(Integer, primary_key=True)
    door_serial = Column(String(20), nullable=False)
    door_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=False)
    final_node = Column(
        String(50), nullable=False
    )  # 'problem_solved', 'service_required', 'not_supported'
    history_steps = Column(JSON, nullable=False)  # Store the full history as JSON

    # Relationship with ServiceTicket
    service_ticket = relationship(
        "ServiceTicket", back_populates="troubleshooting_history", uselist=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the history record to a dictionary."""
        return {
            "id": self.id,
            "door_serial": self.door_serial,
            "door_type": self.door_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "final_node": self.final_node,
            "history_steps": self.history_steps,
        }


class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(Integer, primary_key=True)
    history_id = Column(
        Integer, ForeignKey("troubleshooting_histories.id"), nullable=False
    )
    contact_name = Column(String(100), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    contact_email = Column(String(100), nullable=False)
    priority = Column(String(20), nullable=False)
    additional_info = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(
        String(20), nullable=False, default="open"
    )  # open, assigned, completed
    assigned_to = Column(String(100))  # Email of assigned technician
    last_updated = Column(
        DateTime, onupdate=datetime.now(pytz.timezone("Europe/Berlin"))
    )

    # Relationship with TroubleshootingHistory
    troubleshooting_history = relationship(
        "TroubleshootingHistory", back_populates="service_ticket"
    )

    def to_dict(self, include_history: bool = True) -> Dict[str, Any]:
        """
        Convert the service ticket to a dictionary.

        Args:
            include_history: Whether to include the troubleshooting history

        Returns:
            Dictionary representation of the service ticket
        """
        ticket_dict = {
            "id": self.id,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "priority": self.priority,
            "additional_info": self.additional_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_history and self.troubleshooting_history:
            ticket_dict["history"] = self.troubleshooting_history.to_dict()

        return ticket_dict

    @property
    def json(self) -> Dict[str, Any]:
        """Property that returns the JSON representation of the ticket."""
        return self.to_dict()
