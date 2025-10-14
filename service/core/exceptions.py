"""
Exceptions Module

This module contains all custom exceptions used throughout the Door Service Assistant.
Centralizing exceptions here makes it easier to maintain consistent error handling.
"""


class ServiceError(Exception):
    """Base exception for all Service related errors"""

    pass


# Navigation Errors
class NavigationError(ServiceError):
    """Base exception for navigation-related errors"""

    pass


class InvalidChoiceError(NavigationError):
    """Raised when an invalid choice is made"""

    pass


class NavigationStateError(NavigationError):
    """Raised when navigation state is invalid"""

    pass


# Validation Errors
class ValidationError(ServiceError):
    """Base exception for validation errors"""

    pass


class DoorSerialError(ValidationError):
    """Exception for door serial number validation errors"""

    pass


class DoorTypeError(ValidationError):
    """Exception for door type validation errors"""

    pass


class ErrorCodeValidationError(ValidationError):
    """Exception for error code validation failures"""

    pass


# Service Ticket Errors
class ServiceTicketError(ServiceError):
    """Base exception for service ticket related errors"""

    pass


class ContactValidationError(ServiceTicketError):
    """Exception for contact information validation failures"""

    pass


# Data Errors
class DataError(ServiceError):
    """Base exception for data-related errors"""

    pass


class TreeDataError(DataError):
    """Exception for decision tree data errors"""

    pass


class ConfigurationError(ServiceError):
    """Exception for configuration-related errors"""

    pass
