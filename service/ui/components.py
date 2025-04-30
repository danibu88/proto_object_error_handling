"""
View Components Module

This module contains all view-related components for the TSB Door Service Assistant.
It handles rendering of different screens and UI components while maintaining
separation of concerns from the business logic.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from streamlit_qrcode_scanner import qrcode_scanner
from dataclasses import dataclass
import streamlit as st
import pandas as pd
import logging
import pytz

from service.core.exceptions import ServiceTicketError, ContactValidationError
from service.core.navigator import TreeNavigator
from service.core.validators import DoorValidator

logger = logging.getLogger(__name__)


@dataclass
class ViewContext:
    """Holds context data for view rendering"""

    door_data: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None
    show_debug: bool = False


class ViewManager:
    """
    Manages the rendering of different views and UI components.
    Provides consistent styling and layout across the application.
    """

    @staticmethod
    def show_door_identification() -> None:
        """
        Display the door identification form with QR code scanner option.

        This view allows users to input door serial numbers either manually
        or through QR code scanning.
        """
        st.header("Tür Identifikation")

        # Initialize serial input if not exists
        if "serial_input" not in st.session_state:
            st.session_state.serial_input = ""

        serial = st.text_input(
            "Seriennummer eingeben:",
            key="serial_input",
            help="Format: TSB-X-XXXXX",
            on_change=ViewManager._handle_serial_input_change,
        )

        ViewManager._render_qr_scanner()

        if st.button("Weiter zur Problemanalyse", type="primary"):
            ViewManager._process_door_identification(serial)

    @staticmethod
    def show_troubleshooting() -> None:
        """
        Display the troubleshooting workflow based on current navigation state.

        This view handles the main problem-solving workflow, including:
        - Error code input
        - Step-by-step resolution
        - Navigation options
        """
        try:
            node = st.session_state.navigator.get_current_node()
            current_node_id = st.session_state.navigator.history[-1]

            # Record timestamp for new nodes
            if current_node_id not in st.session_state.history_timestamps:
                st.session_state.history_timestamps[current_node_id] = datetime.now(
                    pytz.timezone("Europe/Berlin")
                )

            # Show door information if available
            if st.session_state.door_data:
                st.info(
                    f"ℹ️ Türtyp: {st.session_state.door_data['door_type']} | Seriennummer: {st.session_state.door_data['serial']}"
                )

            # Show navigation controls
            ViewManager._render_navigation_controls()

            # Check if this is part of a sequence
            if "sequence_metadata" in node:
                ViewManager._render_sequence_node(node)
            else:
                # Handle other node types as before
                node_renderers = {
                    "error_code_input": ViewManager._render_error_code_input,
                    "error_code_details": ViewManager._render_error_code_details,
                    "decision": ViewManager._render_decision_node,
                    "solution": ViewManager._render_solution_node,
                    "action": ViewManager._render_action_node,
                    "end": ViewManager._render_end_node,
                }

                renderer = node_renderers.get(node["type"])
                if renderer:
                    renderer(node)
                else:
                    st.error(f"Unbekannter Knotentyp: {node['type']}")

        except Exception as e:
            logger.error(f"Error in troubleshooting view: {str(e)}", exc_info=True)
            st.error("Ein unerwarteter Fehler ist aufgetreten.")
            if st.button("Neustart"):
                ViewManager._reset_session()
                st.rerun()

    @staticmethod
    def _render_navigation_controls() -> None:
        """Render navigation controls like back button"""
        if st.session_state.navigator.can_go_back():
            col1, col2 = st.columns(2)
            if col1.button("🔄 Neu starten", key="restart"):
                ViewManager._reset_session()
                st.rerun()
            if col2.button("← Zurück"):
                st.session_state.navigator.go_back()
                # reset service form state
                st.session_state.pop("show_service_form", None)
                st.rerun()

    @staticmethod
    def _render_qr_scanner() -> None:
        """Render the QR code scanner component"""
        if "show_scanner" not in st.session_state:
            st.session_state.show_scanner = False

        if not st.session_state.show_scanner:
            if st.button("QR-Code scannen", key="activate_scanner"):
                st.session_state.show_scanner = True
                st.rerun()
        else:
            if st.button("Scanner ausblenden", key="hide_scanner"):
                st.session_state.show_scanner = False
                st.rerun()

            qr_code = qrcode_scanner(key="qrcode_scanner")
            if qr_code:
                ViewManager._process_door_identification(qr_code)

    @staticmethod
    def _render_error_code_input(node: Dict[str, Any]) -> None:
        """
        Render the error code input form
        """
        if "error_code_input" not in st.session_state:
            st.session_state.error_code_input = ""

        col1, col2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
        # Show error code input form
        with col1:
            st.text_input(
                "Fehlercode eingeben:",
                key="error_code_input",
                help="Geben Sie den angezeigten Fehlercode ein oder wählen sie einen Code aus der Liste (z.B. 10).",
            )
        # Show button to check error code
        with col2:
            if st.button("Fehlercode prüfen", type="primary"):
                error_code = st.session_state.error_code_input
                ViewManager._process_error_code(error_code)
        # Show available error codes
        ViewManager._render_error_code_list()

    @staticmethod
    def _render_error_code_list() -> None:
        """Render the list of available error codes"""
        available_codes = st.session_state.navigator.troubleshooting_tree["nodes"][
            "error_code_input"
        ]["available_error_codes"]

        # Create columns for better layout
        for i in range(0, len(available_codes), 2):
            col1, col2 = st.columns(2)

            # First column
            code = available_codes[i]
            node_data = st.session_state.navigator.troubleshooting_tree["nodes"][
                f"error_code_{code}"
            ]
            ViewManager._render_error_code_button(col1, code, node_data)

            # Second column (if exists)
            if i + 1 < len(available_codes):
                code = available_codes[i + 1]
                node_data = st.session_state.navigator.troubleshooting_tree["nodes"][
                    f"error_code_{code}"
                ]
                ViewManager._render_error_code_button(col2, code, node_data)

    @staticmethod
    def _render_error_code_details(node: Dict[str, Any]) -> None:
        """Render error code details and start sequence"""
        st.markdown(f"### Fehlercode {node['error_code']}")

        with st.expander("Fehler Details", expanded=True):
            st.write(f"**Beschreibung:** {node['description']}")
            st.write(f"**Problem:** {node['problem']}")
            st.info(f"**Kontext:** {node['context']}")

        if st.button("Mit Fehlerbehebung beginnen", type="primary"):
            next_node = node["next_node"]
            st.session_state.navigator.history.append(next_node)
            st.session_state.history_timestamps[next_node] = datetime.now(
                pytz.timezone("Europe/Berlin")
            )
            st.rerun()

    @staticmethod
    def _render_sequence_node(node: Dict[str, Any]) -> None:
        """
        Render a node that is part of a sequence
        """
        sequence_metadata = node.get("sequence_metadata", {})
        if sequence_metadata:
            # Show sequence progress
            total_steps = sequence_metadata["total_steps"]
            current_step = sequence_metadata["current_step"]
            sequence_name = sequence_metadata["sequence_name"]

            st.markdown(f"### {sequence_name}")
            progress = ViewManager._calculate_progress(current_step, total_steps)
            st.progress(progress)
            st.write(f"Schritt {current_step} von {total_steps}")

        # Show the actual node content
        st.markdown(f"### {node['text']}")

        # Show context if available
        if "context" in node:
            with st.expander("Details", expanded=True):
                st.info(node["context"])

        # Handle options
        for option in node.get("options", []):
            if st.button(option["text"]):
                st.session_state.navigator.responses[node["id"]] = option["text"]
                if "next_node" in option:
                    next_node = option["next_node"]
                    st.session_state.navigator.history.append(next_node)
                    st.session_state.history_timestamps[next_node] = datetime.now(
                        pytz.timezone("Europe/Berlin")
                    )
                    st.rerun()

    @staticmethod
    def _render_error_code_button(column: Any, code: str, data: Dict[str, Any]) -> None:
        """
        Render a single error code button with description

        Args:
            column: Streamlit column object
            code: Error code
            data: Error code data
        """
        with column:
            description = data.get("description", "Keine Beschreibung verfügbar")
            if st.button(
                f"Code {code}",
                key=f"error_code_{code}",
                help=description,
                use_container_width=True,
            ):
                ViewManager._process_error_code(code)
            # st.caption(description)

    @staticmethod
    def _render_error_code_steps() -> None:
        """Render the steps for error resolution"""
        current_node = st.session_state.navigator.get_current_node()
        sequence_metadata = st.session_state.navigator.get_sequence_metadata(
            current_node
        )

        # Show context information
        with st.expander("Fehler Details", expanded=True):
            st.info(f"Fehlercode: {error_code}")
            if "description" in error_data:
                st.write(f"Beschreibung: {error_data['description']}")
            if "context" in error_data:
                st.write(f"Kontext: {error_data['context']}")

        if sequence_metadata:
            # Show context information from error code
            if "context" in current_node:
                with st.expander("Details", expanded=True):
                    st.info(current_node["context"])

            # Show progress
            total_steps = sequence_metadata["total_steps"]
            current_step = sequence_metadata["current_step"]
            sequence_name = sequence_metadata["sequence_name"]

            # Show progress bar
            progress = ViewManager._calculate_progress(current_step, total_steps)
            st.progress(progress)
            st.write(f"Schritt {current_step} von {total_steps}: {sequence_name}")

            # Show current step
            st.markdown(f"### {current_node['text']}")

            # Record timestamp for history
            if current_node not in st.session_state.history_timestamps:
                st.session_state.history_timestamps[current_node] = datetime.now(
                    pytz.timezone("Europe/Berlin")
                )

            # Render the options for this step
            for option in current_node.get("options", []):
                if st.button(option["text"]):
                    st.session_state.navigator.make_choice(option["text"])
                    st.rerun()

        else:
            # Handle non-sequence nodes normally
            st.markdown(f"### {current_node['text']}")
            for option in current_node.get("options", []):
                if st.button(option["text"]):
                    st.session_state.navigator.make_choice(option["text"])
                    st.rerun()

    @staticmethod
    def _render_step_options(current_step_data: Dict[str, Any]) -> None:
        """
        Render navigation options for the current step
        """
        navigator = st.session_state.navigator

        # Get sequence metadata if it exists
        sequence_metadata = navigator.get_sequence_metadata(current_step_data)

        # If this is part of a sequence, show progress
        if sequence_metadata:
            progress = ViewManager._calculate_progress(
                sequence_metadata["current_step"], sequence_metadata["total_steps"]
            )
            st.progress(progress)
            st.write(
                f"Schritt {sequence_metadata['current_step']} von {sequence_metadata['total_steps']}"
            )

        # Handle the options
        for option in current_step_data.get("options", []):
            if st.button(option["text"]):
                # Store the user's choice for history
                navigator.responses[current_step_data] = option["text"]

                if "next_node" in option:
                    next_node = option["next_node"]
                    navigator.history.append(next_node)
                    st.session_state.history_timestamps[next_node] = datetime.now(
                        pytz.timezone("Europe/Berlin")
                    )
                    st.rerun()

    @staticmethod
    def _render_decision_node(node: Dict[str, Any]) -> None:
        """
        Render a decision node with its options

        Args:
            node: Current node data
        """
        st.markdown(f"### {node['text']}")

        # render image if available
        if "image" in node:
            _, center, _ = st.columns([1, 2, 1])
            with center:
                st.image(
                    Path(__file__).parent.parent / "data" / node["image"],
                    use_container_width=True,
                )

        for option in node.get("options", []):
            if st.button(option["text"], key=option["text"]):
                if "next_node" in option:
                    next_node = option["next_node"]
                    st.session_state.navigator.history.append(next_node)
                    st.session_state.navigator.responses[node["id"]] = option["text"]
                    st.session_state.history_timestamps[next_node] = datetime.now(
                        pytz.timezone("Europe/Berlin")
                    )
                    st.rerun()
                else:
                    st.session_state.navigator.make_choice(option["text"])
                    st.rerun()

    @staticmethod
    def _render_solution_node(node: Dict[str, Any]) -> None:
        """
        Render a solution node with next steps

        Args:
            node: Current node data
        """
        st.markdown(f"### {node['text']}")

        if st.button("🆕 Neue Problemanalyse starten"):
            ViewManager._reset_session()
            st.rerun()

    @staticmethod
    def _render_action_node(node: Dict[str, Any]) -> None:
        """
        Render an action node with its options

        Args:
            node: Current node data
        """
        st.markdown(f"### {node['text']}")

        for option in node.get("options", []):
            if st.button(option["text"], key=option["text"]):
                st.session_state.navigator.make_choice(option["text"])
                st.rerun()

    # Update the _render_end_node method to save history
    @staticmethod
    def _render_end_node(node: Optional[Dict[str, Any]] = None) -> None:
        """Render the end screen with summary and options"""
        if st.session_state.door_data and "timestamp" in st.session_state.door_data:
            start_time = datetime.fromisoformat(st.session_state.door_data["timestamp"])
            st.write(
                f"Anfrage erstellt am {ViewManager._format_timestamp(start_time, show_date=True)}"
            )

        history = ViewManager._collect_history()

        # Save troubleshooting session
        final_node = (
            st.session_state.navigator.history[-1]
            if st.session_state.navigator.history
            else None
        )

        # Write final node as 'not_supported' if final_node is None and door_id validation fails
        is_valid, door_type, message = DoorValidator.validate_door_serial(
            st.session_state.door_data["serial"]
        )
        if not is_valid:
            final_node = "not_supported"

        if not st.session_state.get("history_id", None):
            # write to DB
            history_id = ViewManager._save_troubleshooting_session(
                st.session_state.door_data, history, final_node
            )
            # write history_id to session state
            st.session_state.history_id = history_id

        # service form default state
        if "show_service_form" not in st.session_state:
            st.session_state.show_service_form = False
            if st.session_state.get("show_service_form", False) or (
                node
                and "service" in node.get("id", "").lower()
                or st.session_state.create_service_ticket
            ):
                st.session_state.show_service_form = True

        if node:
            if "problem_solved" in node.get("id", ""):
                st.success("🎉 Problem erfolgreich behoben!")
            else:
                st.warning("⚠️ Problem konnte nicht vollständig gelöst werden")
                st.info(
                    "Bitte erstellen Sie ein Service-Ticket für weitere Unterstützung."
                )

            ViewManager._render_history_section(history)

            # Create columns for action buttons with top alignment
            col1, col2 = st.columns(2)

            # Ensure both columns start at the same height with containers
            with col1.container():
                if history:
                    df = pd.DataFrame(history)
                    df.columns = ["Zeitpunkt", "Schritt", "Antwort", "Knoten-ID"]
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "📥 Bericht herunterladen",
                        csv,
                        "troubleshooting_report.csv",
                        "text/csv",
                        key="download-csv",
                        help="Laden Sie einen CSV-Bericht der Fehlerdiagnose herunter",
                        use_container_width=True,
                    )

            with col2.container():
                st.button(
                    "🎫 Service-Ticket erstellen",
                    key="create_ticket",
                    use_container_width=True,
                    disabled=st.session_state.show_service_form,
                    on_click=lambda: setattr(
                        st.session_state, "show_service_form", True
                    ),
                )

        # Show service ticket form only if button was clicked or if service is required
        if st.session_state.show_service_form:
            ViewManager._render_service_ticket_section(
                st.session_state.door_data, history
            )

        if st.button("🆕 Neue Problemanalyse starten"):
            ViewManager._reset_session()
            st.rerun()

    @staticmethod
    def show_end_node() -> None:
        """Public interface for rendering the end screen"""
        ViewManager._render_end_node()

    @staticmethod
    def _collect_history() -> List[Dict[str, Any]]:
        """
        Collect the troubleshooting history.
        """
        history = []
        navigator = st.session_state.navigator

        # Keep track if we're in an error code sequence
        current_error_code = None

        # Process all nodes in the history
        for node_id in navigator.history:
            try:
                # Get node directly from troubleshooting tree
                node = navigator.troubleshooting_tree["nodes"].get(node_id)
                if not node:
                    logger.info(f"Node not found: {node_id}")
                    continue
                if node and "text" not in node:
                    logger.info(f"Missing text: {node_id}")
                    # Check if we're entering an error code sequence
                    if node.get("type") == "error_code_details":
                        current_error_code = node.get("error_code")
                    continue

                timestamp = st.session_state.history_timestamps.get(
                    node_id, datetime.now(pytz.timezone("Europe/Berlin"))
                )
                node_text = node["text"]
                response = navigator.responses.get(node_id, "✅")

                # Add error code prefix to sequence steps if we're in an error code sequence
                if current_error_code and node.get("sequence_metadata"):
                    node_text = f"[{current_error_code}: Schritt {node['sequence_metadata']['current_step']}/{node['sequence_metadata']['total_steps']}] {node_text}]"

                history_entry = {
                    "raw_timestamp": timestamp,
                    "timestamp": ViewManager._format_timestamp(timestamp),
                    "node_text": node_text,
                    "response": response,
                    "id": node_id,
                }
                history.append(history_entry)

            except Exception as e:
                logger.error(f"Error processing node {node_id}: {str(e)}")

        # Sort history by raw timestamp
        history.sort(key=lambda x: x["raw_timestamp"])

        # Remove raw_timestamp from entries after sorting
        for entry in history:
            del entry["raw_timestamp"]

        return history

    @staticmethod
    def _get_node_from_history(node_id: str, node_tree: str) -> Dict[str, Any]:
        """
        Get node data from navigation history

        Args:
            node_id: ID of the node to retrieve
            node_tree: Name of the tree containing the node

        Returns:
            Node data dictionary

        Raises:
            KeyError: If node is not found
        """
        navigator = st.session_state.navigator
        try:
            return navigator.troubleshooting_tree["nodes"][node_id]
        except KeyError:
            raise KeyError(f"Node not found: {node_id}")

    @staticmethod
    def _format_timestamp(dt: datetime, show_date: bool = False) -> str:
        """
        Format timestamp according to locale

        Args:
            dt: Datetime to format
            show_date: Whether to include the date

        Returns:
            Formatted timestamp string
        """
        if show_date:
            return dt.strftime("%A, %d. %B %Y")
        return dt.strftime("%H:%M:%S")

    @staticmethod
    def _calculate_progress(current: int, total: int) -> float:
        """
        Calculate progress ensuring value is between 0 and 1

        Args:
            current: Current step number
            total: Total number of steps

        Returns:
            Progress value between 0 and 1
        """
        if total <= 0:
            return 0.0
        return min(max(current / total, 0.0), 1.0)

    @staticmethod
    def _process_error_code(code: str) -> None:
        """
        Process an entered error code

        Args:
            code: Error code to process
        """
        try:
            available_codes = st.session_state.navigator.troubleshooting_tree["nodes"][
                "error_code_input"
            ]["available_error_codes"]
            if code in available_codes:
                error_node_id = f"error_code_{code}"

                # Store error code in session for reference
                st.session_state.current_error_code = code

                # Navigate to error code node
                st.session_state.navigator.history.append(error_node_id)
                # Store the error code choice
                st.session_state.navigator.responses["error_code_input"] = code
                st.session_state.history_timestamps["error_code_input"] = datetime.now(
                    pytz.timezone("Europe/Berlin")
                )
                st.rerun()
            else:
                # end troubleshooting if error code is not valid and move to end node with service form
                next_node = "service_required"
                st.session_state.navigator.history.append(next_node)
                st.session_state.navigator.responses["error_code_input"] = code
                st.session_state.history_timestamps[next_node] = datetime.now(
                    pytz.timezone("Europe/Berlin")
                )
                st.rerun()

        except Exception as e:
            st.error(f"Fehler bei der Verarbeitung: {str(e)}")

    @staticmethod
    def _process_door_identification(serial: str) -> None:
        """
        Process door identification input

        Args:
            serial: Door serial number to process
        """
        if "create_service_ticket" not in st.session_state:
            st.session_state.create_service_ticket = False  # Initialize if not exists

        is_valid, door_type, message = DoorValidator.validate_door_serial(serial)

        if not is_valid:
            st.error(message)
            st.session_state.step = "end"
            st.session_state.create_service_ticket = True
            st.session_state.door_data = {
                "serial": serial,
                "door_type": door_type,
                "timestamp": datetime.now(pytz.timezone("Europe/Berlin")).isoformat(),
            }

            if door_type:  # If it's a valid TSB door but wrong type
                st.info("Möchten Sie ein Service-Ticket erstellen?")
                if st.button("Service-Ticket erstellen"):
                    st.rerun()
        else:
            st.session_state.door_data = {
                "serial": serial,
                "door_type": door_type,
                "timestamp": datetime.now(pytz.timezone("Europe/Berlin")).isoformat(),
            }
            st.session_state.step = "troubleshoot"
            st.session_state.navigator.start()
            st.rerun()

    @staticmethod
    def _handle_serial_input_change() -> None:
        """Handle changes to the serial input field"""
        st.session_state.step = "identify"

    @staticmethod
    def _reset_session() -> None:
        """Reset the session state to initial values"""
        st.session_state.clear()
        st.session_state.navigator = TreeNavigator()
        st.session_state.create_service_ticket = False  # Initialize the flag

    @staticmethod
    def _render_history_section(history: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Render the troubleshooting history section
        """
        if not history:
            return

        st.subheader("Zusammenfassung der durchgeführten Schritte")

        # Create DataFrame for display
        df = pd.DataFrame(history)
        # drop node id column
        df.drop("id", axis=1, inplace=True)

        # Enhance history with sequence information
        if "node_text" in df.columns:

            def add_sequence_info(row):
                return row["node_text"]

            df["node_text"] = df.apply(add_sequence_info, axis=1)

        df.set_index("timestamp", inplace=True)
        df.index = pd.to_datetime(df.index, format="%H:%M:%S").strftime("%H:%M:%S")
        df.index.name = "Zeitpunkt"
        df.columns = ["Schritt", "Status"]

        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Schritt": st.column_config.TextColumn("Schritt", width="large"),
                "Status": st.column_config.TextColumn(
                    "Status",
                    width="small",
                    help="✓ bedeutet dieser Schritt wurde abgeschlossen",
                ),
            },
        )

    @staticmethod
    def _render_service_ticket_section(
        door_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Render the service ticket creation form

        Args:
            door_data: Optional door information
            history: Optional troubleshooting history
        """
        st.subheader("Service-Ticket erstellen")

        with st.form("service_ticket", clear_on_submit=True):
            st.write("Bitte geben Sie Ihre Kontaktdaten ein:")

            # Door information section
            door_id = door_data.get("serial", "") if door_data else ""
            door_type = door_data.get("door_type", "") if door_data else ""

            col1, col2 = st.columns(2)
            with col1:
                st.text_input(
                    "Tür-Seriennummer",
                    value=door_id,
                    disabled=bool(door_data),
                    help="Format: TSB-X-XXXXX" if not door_data else None,
                    key="ticket_door_id",
                )
            with col2:
                st.text_input(
                    "Türtyp",
                    value=door_type,
                    disabled=bool(door_data),
                    help="Schiebetür, Drehtür, etc." if not door_data else None,
                    key="ticket_door_type",
                )

            # Contact information section
            st.subheader("Kontaktdaten")
            col1, col2 = st.columns(2)
            with col1:
                contact_name = st.text_input(
                    "Kontaktperson*",
                    key="ticket_contact_name",
                    help="Name der Ansprechperson",
                )
                contact_phone = st.text_input(
                    "Telefonnummer*",
                    key="ticket_contact_phone",
                    help="Erreichbare Telefonnummer",
                )
            with col2:
                contact_email = st.text_input(
                    "E-Mail*",
                    key="ticket_contact_email",
                    help="E-Mail-Adresse für Rückfragen",
                )

            # Additional information
            st.subheader("Weitere Informationen")
            additional_info = st.text_area(
                "Zusätzliche Informationen",
                help="Weitere relevante Details zum Problem",
                key="ticket_additional_info",
            )

            hint_map = {
                0: "3-5 Werktagen",
                1: "1-2 Werktagen",
                2: "am selben Tag (Extra-Gebühr)",
            }

            # Priority selection
            priority = st.segmented_control(
                "Priorität",
                options=["Niedrig", "Mittel", "Hoch"],
                default="Mittel",
                help="Wählen Sie die Dringlichkeit Ihres Anliegens",
            )
            st.write(f"ℹ️ Niedrig: Bearbeitung in {hint_map[0]}")
            st.write(f"ℹ️ Mittel: Bearbeitung in {hint_map[1]}")
            st.write(f"ℹ️ Hoch: Bearbeitung {hint_map[2]}")

            # Submit button
            submitted = st.form_submit_button(
                "Service-Ticket erstellen", type="primary", use_container_width=True
            )

            if submitted:
                if not all([contact_name, contact_phone, contact_email]):
                    st.error("Bitte füllen Sie alle Pflichtfelder (*) aus.")
                else:
                    ViewManager._create_service_ticket(
                        contact_data={
                            "name": contact_name,
                            "phone": contact_phone,
                            "email": contact_email,
                        },
                        additional_info=additional_info,
                        priority=priority,
                        door_id=door_id or st.session_state.ticket_door_id,
                        door_type=door_type or st.session_state.ticket_door_type,
                        history_id=st.session_state.history_id,
                    )

    @staticmethod
    def _save_troubleshooting_session(
        door_data: Dict[str, Any], history: List[Dict[str, Any]], final_node: str
    ) -> Optional[int]:
        """
        Save the troubleshooting session to the database.

        Returns:
            Optional[int]: The history ID if saved successfully
        """
        try:
            from tsb_door_service.database.operations import (
                save_troubleshooting_history,
                get_session,
            )

            # Get start time from door_data
            start_time = datetime.fromisoformat(door_data["timestamp"])
            # Use current time as end time
            end_time = datetime.now(pytz.timezone("Europe/Berlin"))

            db = next(get_session())
            history_record = save_troubleshooting_history(
                db=db,
                door_serial=door_data["serial"],
                door_type=door_data["door_type"],
                start_time=start_time,
                end_time=end_time,
                final_node=final_node,
                history_steps=history,
            )

            return history_record.id

        except Exception as e:
            logger.error(f"Failed to save troubleshooting history: {str(e)}")
            return None

    @staticmethod
    def _create_service_ticket(
        contact_data: Dict[str, str],
        additional_info: str,
        priority: str,
        door_id: Optional[str] = None,
        door_type: Optional[str] = None,
        history_id: Optional[int] = None,
    ) -> bool:
        """
        Create a service ticket in the database. Supports both direct creation and
        creation with troubleshooting history.

        Args:
            contact_data: Dictionary containing contact information
            additional_info: Additional ticket information
            priority: Ticket priority level
            door_id: Optional door serial number (for direct creation)
            door_type: Optional door type (for direct creation)
            history_id: Optional troubleshooting history ID

        Returns:
            bool: True if ticket was created successfully
        """
        try:
            from tsb_door_service.database.operations import (
                create_service_ticket,
                create_direct_service_ticket,
                get_session,
            )

            db = next(get_session())

            if history_id:
                # Create ticket with history reference
                ticket_data = create_service_ticket(
                    db=db,
                    history_id=history_id,
                    contact_name=contact_data["name"],
                    contact_phone=contact_data["phone"],
                    contact_email=contact_data["email"],
                    priority=priority,
                    additional_info=additional_info,
                )
            else:
                # Create ticket directly without history
                ticket_data = create_direct_service_ticket(
                    db=db,
                    door_serial=door_id,
                    door_type=door_type,
                    contact_name=contact_data["name"],
                    contact_phone=contact_data["phone"],
                    contact_email=contact_data["email"],
                    priority=priority,
                    additional_info=additional_info,
                )

            st.success(
                "✅ Service-Ticket wurde erstellt! "
                "Sie erhalten in Kürze eine Bestätigung per E-Mail."
            )

            # Show ticket details in expandable section
            with st.expander("Ticket Details", expanded=False):
                st.json(ticket_data.to_dict())

            return True
        except (ServiceTicketError, ContactValidationError) as e:
            logger.error(f"Error creating service ticket: {str(e)}")
            st.error("Fehler bei der Erstellung des Service-Tickets.")
            return False
