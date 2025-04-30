"""
Validators Module

This module provides validation functionality for the TSB Door Service Assistant.
It includes validators for door serial numbers, error codes, and other input data.
"""

from typing import Tuple, Dict, Any, Optional
from enum import Enum, auto
import re
import logging

from service.core.exceptions import (
    ValidationError,
    DoorSerialError,
    DoorTypeError,
)

logger = logging.getLogger(__name__)


class DoorType(Enum):
    """Enumeration of supported door types"""

    SLIDING = auto()
    REVOLVING = auto()
    SWING = auto()


# Mapping of door type codes to (name, enum) pairs
DOOR_TYPE_MAPPING = {
    "S": ("Schiebetür", DoorType.SLIDING),
    "D": ("Drehtür", DoorType.SWING),
    "K": ("Karusselltür", DoorType.REVOLVING),
}


class DoorValidator:
    """
    Validator for door-related input data.
    Handles validation of serial numbers, types, and other door-specific data.
    """

    SERIAL_PATTERN = re.compile(r"^TSB-[SDK]-\d{5}$")

    @classmethod
    def validate_door_serial(cls, serial: str) -> Tuple[bool, str, str]:
        """
        Validate a door serial number.

        Args:
            serial: The door serial number to validate

        Returns:
            Tuple containing:
                - Boolean indicating if the serial is valid
                - String containing the door type name
                - String containing a validation message

        Example:
            >>> DoorValidator.validate_door_serial("TSB-S-12345")
            (True, "Schiebetür", "Gültige TSB Schiebetür")
        """
        try:
            if not serial:
                raise DoorSerialError("Bitte geben Sie eine Seriennummer ein.")

            # Clean and normalize input
            serial = cls._normalize_serial(serial)

            # Validate format
            if not cls.SERIAL_PATTERN.match(serial):
                raise DoorSerialError(
                    "Ungültiges Format. Erwartetes Format: TSB-X-XXXXX"
                )

            # Extract and validate door type
            door_type_code = serial.split("-")[1]
            if door_type_code not in DOOR_TYPE_MAPPING:
                raise DoorTypeError(f"Ungültiger Türtyp-Code: {door_type_code}")

            door_type_name, _ = DOOR_TYPE_MAPPING[door_type_code]

            # Currently only supporting sliding doors
            if door_type_code != "S":
                return (
                    False,
                    door_type_name,
                    f"Selbstdiagnose ist derzeit nur für TSB Schiebetüren verfügbar. "
                    f"Ihr Türtyp: {door_type_name}",
                )

            return True, door_type_name, "Gültige TSB Schiebetür"

        except ValidationError as e:
            return False, "", str(e)
        except Exception as e:
            logger.error(f"Unexpected error during door validation: {str(e)}")
            return False, "", "Ein unerwarteter Fehler ist aufgetreten."

    @staticmethod
    def _normalize_serial(serial: str) -> str:
        """
        Normalize a serial number by removing whitespace and converting to uppercase.

        Args:
            serial: Serial number to normalize

        Returns:
            Normalized serial number
        """
        return serial.strip().upper()


class ErrorCodeValidator:
    """
    Validator for error codes and related input.
    """

    @staticmethod
    def validate_error_code(code: str, available_codes: Dict[str, Any]) -> bool:
        """
        Validate an error code against available codes.

        Args:
            code: Error code to validate
            available_codes: Dictionary of valid error codes and their data

        Returns:
            Boolean indicating if the code is valid
        """
        try:
            # Clean input
            code = code.strip().upper()

            # Check if code exists
            if code not in available_codes:
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating error code: {str(e)}")
            return False


class ServiceTicketValidator:
    """
    Validator for service ticket input data.
    """

    @staticmethod
    def validate_contact_data(
        contact_data: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate contact information for service tickets.

        Args:
            contact_data: Dictionary containing contact information

        Returns:
            Tuple containing:
                - Boolean indicating if data is valid
                - Optional error message
        """
        required_fields = ["name", "phone", "email"]

        # Check required fields
        missing_fields = [
            field
            for field in required_fields
            if not contact_data.get(field, "").strip()
        ]

        if missing_fields:
            return False, f"Fehlende Pflichtfelder: {', '.join(missing_fields)}"

        # Validate email format
        email = contact_data.get("email", "").strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return False, "Ungültige E-Mail-Adresse"

        # Validate phone format (basic check)
        phone = contact_data.get("phone", "").strip()
        if not re.match(r"^\+?[\d\s-]{8,}$", phone):
            return False, "Ungültige Telefonnummer"

        return True, None

    @staticmethod
    def validate_priority(priority: str) -> bool:
        """
        Validate ticket priority level.

        Args:
            priority: Priority level to validate

        Returns:
            Boolean indicating if priority is valid
        """
        valid_priorities = {"Niedrig", "Mittel", "Hoch"}
        return priority in valid_priorities
