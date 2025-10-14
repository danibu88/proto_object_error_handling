"""
Tree Navigator Module

This module provides navigation functionality through decision trees for the Door Service Assistant.
It handles both general door problem diagnosis and specific error code resolution workflows.

The module supports:
- Navigation through decision trees
- Error code step handling
- History tracking
- Backwards navigation
- State management

Dependencies:
- door-problems.json
- error-codes.json
"""

from typing import Dict, List, Optional, Any, Union, TypedDict
from dataclasses import dataclass
from enum import Enum, auto
import json
import logging
from pathlib import Path
from datetime import datetime
import pytz
import streamlit as st

from service.core.exceptions import (
    InvalidChoiceError,
    NavigationStateError,
)

# Configure logging
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Enumeration of possible node types in the decision tree"""

    DECISION = auto()
    ACTION = auto()
    SOLUTION = auto()
    ERROR_CODE_INPUT = auto()
    ERROR_CODE_STEP = auto()
    END = auto()


@dataclass
class Option:
    """Represents a navigation option in a node"""

    text: str
    next_node: Optional[str] = None


class Node(TypedDict):
    """TypedDict representing a node in the decision tree"""

    type: str
    text: str
    options: List[Dict[str, str]]
    context: Optional[str]
    description: Optional[str]
    total_steps: Optional[int]
    current_step: Optional[int]
    image: Optional[str]


class TreeNavigator:
    """
    Handles navigation through decision trees for door problem diagnosis
    and error code resolution.
    """

    def __init__(self, data_dir: Union[str, Path] = None):
        """Initialize the TreeNavigator with decision trees from JSON files."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Get the absolute path to the data directory relative to this file
            self.data_dir = Path(__file__).parent.parent / "data"

        self.troubleshooting_tree: Dict[str, Any] = {}
        self.history: List[str] = []
        self.responses: Dict[str, Any] = {}

        try:
            self._load_trees()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load decision trees: {str(e)}")
            raise

    def _load_trees(self) -> None:
        """Load decision trees from JSON files"""
        try:
            troubleshooting_path = self.data_dir / "troubleshooting.json"

            if not troubleshooting_path.exists():
                raise FileNotFoundError(f"Could not find file: {troubleshooting_path}")

            with troubleshooting_path.open("r", encoding="utf-8") as f:
                self.troubleshooting_tree = json.load(f)

            self._validate_trees()

        except FileNotFoundError as e:
            logger.error(f"Decision tree file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in decision tree file: {str(e)}")
            raise

    def _validate_trees(self) -> None:
        """
        Validate the structure of loaded decision trees.

        Raises:
            ValueError: If tree structure is invalid
        """
        required_keys = {"nodes"}
        if not all(key in self.troubleshooting_tree for key in required_keys):
            raise ValueError("Invalid tree structure")
        if "root" not in self.troubleshooting_tree["nodes"]:
            raise ValueError("Missing root node")

    def start(self) -> Node:
        """
        Start navigation at the root node of the door problems tree.

        Returns:
            Dict containing the root node data
        """
        self.history = ["root"]
        self.responses = {}
        return self.get_current_node()

    def get_current_node(self) -> Node:
        """
        Get the current node's data.

        Returns:
            Dict containing the current node data

        Raises:
            NavigationStateError: If current node is invalid
        """
        try:
            current_id = self.history[-1]
            return self.troubleshooting_tree["nodes"][current_id]
        except (KeyError, IndexError) as e:
            logger.error(
                f"Navigation error: Node {self.history[-1] if self.history else 'None'} not found"
            )
            raise NavigationStateError("Invalid navigation state") from e

    def can_go_back(self) -> bool:
        """Check if backward navigation is possible"""
        return len(self.history) > 1

    def go_back(self) -> Node:
        """
        Navigate back one step.

        Returns:
            Dict containing the previous node data

        Raises:
            NavigationStateError: If navigation back is not possible
        """
        if not self.can_go_back():
            raise NavigationStateError("Cannot go back from root node")

        self.history.pop()
        last_node = self.history[-1]
        self.responses.pop(last_node, None)

        return self.get_current_node()

    def make_choice(self, choice: str) -> Node:
        """
        Process a user choice and navigate to the next node.

        Args:
            choice: The selected option text

        Returns:
            Dict containing the next node data

        Raises:
            InvalidChoiceError: If the choice is invalid for the current node
        """
        try:
            current_node = self.get_current_node()
            current_node_id = self.history[-1]

            # Store the response before changing nodes
            self.responses[current_node_id] = choice

            if current_node["type"] == NodeType.ERROR_CODE_STEP.name:
                return self._handle_error_code_step_choice(current_node, choice)

            if current_node["type"] == NodeType.ERROR_CODE_INPUT.name:
                return self._handle_error_code_input(choice)

            return self._handle_standard_choice(current_node, choice)

        except KeyError as e:
            raise InvalidChoiceError(f"Invalid choice: {choice}") from e

    def _handle_error_code_step_choice(self, node: Node, choice: str) -> Node:
        """Handle choices within error code resolution steps"""
        # Find matching option for the choice
        for option in node.get("options", []):
            if option["text"] == choice:
                if "next_node" in option:
                    next_node = option["next_node"]
                    self.history.append(next_node)
                    return self.get_current_node()
                break

        raise InvalidChoiceError(f"Invalid choice for error code step: {choice}")

    def _handle_error_code_input(self, error_code: str) -> Node:
        """Handle error code input and start error resolution flow"""
        try:
            if (
                error_code
                not in self.troubleshooting_tree["nodes"]["error_code_input"][
                    "error_codes"
                ]
            ):
                raise InvalidChoiceError(f"Invalid error code: {error_code}")

            # todo: check if we need / how we do this. Store error code in responses
            # self.responses["root_ec"] = error_code

            error_code_data = self.troubleshooting_tree["nodes"]["error_code_input"][
                "error_codes"
            ][error_code]

            # Navigate to the first node in the error code's sequence
            next_node = error_code_data["next_node"]
            self.history.append(next_node)
            return self.get_current_node()

        except Exception as e:
            logger.error(f"Error handling error code input: {str(e)}")
            raise

    def _handle_standard_choice(self, node: Node, choice: str) -> Node:
        """Handle standard navigation choices"""
        for option in node.get("options", []):
            if option["text"] == choice:
                if "next_node" in option:
                    next_node = option["next_node"]

                    # Check which tree contains the next node
                    if "next_node" in option:
                        next_node = option["next_node"]
                        self.history.append(next_node)
                        st.session_state.history_timestamps[next_node] = datetime.now(pytz.timezone("Europe/Berlin"))

                    try:
                        return self.get_current_node()
                    except NavigationStateError:
                        # Fallback to problem solved if navigation fails
                        logger.error(f"Failed to navigate to node: {next_node}")
                        self.history.append("problem_solved")  # Fallback
                        return self.get_current_node()

        raise InvalidChoiceError(f"Invalid choice: {choice}")

    def _handle_error_code_steps(self, error_code_data: Dict[str, Any]) -> Node:
        """
        Convert error code steps into a consistent node format.
        """
        if "steps" not in error_code_data:
            self.history = ["problem_solved"]
            return self.get_current_node()

        current_step = error_code_data["steps"][0]

        # Generate a unique node ID for this step
        step_node_id = f"error_step_{error_code_data.get('description', 'step')}_1"
        self.history.append(step_node_id)
        st.session_state.history_timestamps[step_node_id] = datetime.now(pytz.timezone("Europe/Berlin"))

        # Initialize response for first step
        self.responses[step_node_id] = ""  # Will be updated when choice is made

        return {
            "type": NodeType.ERROR_CODE_STEP.name,
            "text": current_step["text"],
            "context": error_code_data.get("context", ""),
            "description": error_code_data.get("description", ""),
            "total_steps": len(error_code_data["steps"]),
            "current_step": 1,
            "options": (
                current_step.get("options", [])
                if "options" in current_step
                else [{"text": "Weiter", "next_step": "step_2"}]
            ),
        }

    def get_sequence_metadata(self, node_id: str) -> Dict[str, Any]:
        """
        Get sequence metadata for a node if it exists.

        Args:
            node_id: Current node ID

        Returns:
            Dictionary containing sequence metadata (total_steps, current_step, sequence_name)
            or empty dict if node is not part of a sequence
        """
        try:
            node = self.troubleshooting_tree["nodes"][node_id]
            return node.get("sequence_metadata", {})
        except KeyError:
            return {}
