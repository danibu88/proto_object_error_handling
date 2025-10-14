"""
Door Service Assistant - Main Application

This is the main entry point for the Door Service Assistant application.
It handles application initialization, routing, and overall state management.

Dependencies:
- streamlit
- tree_navigator (custom module for decision tree navigation)
- view_components (custom module for UI components)
- validators (custom module for input validation)

Environment Variables:
    DEBUG: Enable debug mode (default: False)
    LOG_LEVEL: Logging level (default: INFO)
    DATA_DIR: Directory containing decision tree data files (default: ./data)

Version: 1.1
"""

import os
import logging
from typing import Dict, Any
import streamlit as st
from pathlib import Path
import locale

# Custom modules
from service.core.navigator import TreeNavigator
from service.core.exceptions import (
    NavigationError,
    ValidationError,
)
from service.ui.components import ViewManager
from service.ui.analytics import show_analytics
from service.ui.ticketing import show_ticketing
from service.ui.chat import render_chat_widget

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Application configuration
APP_CONFIG = {
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "data_dir": Path(__file__).parent / "data",
    "locale": "de_DE.UTF-8",
    "page_title": "Tür Service",
    "page_icon": "🚪",
}


class ServiceAssistant:
    """
    Main application class for the Door Service Assistant.
    Handles initialization, routing, and state management.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the application with the given configuration.

        Args:
            config: Dictionary containing application configuration
        """
        self.config = config
        self.setup_locale()
        self.setup_streamlit()
        self.init_session_state()

    def setup_locale(self) -> None:
        """Configure locale settings for internationalization"""
        try:
            locale.setlocale(locale.LC_TIME, self.config["locale"])
        except locale.Error as e:
            logger.warning(f"Failed to set locale {self.config['locale']}: {str(e)}")
            logger.info("Falling back to system default locale")

    def setup_streamlit(self) -> None:
        """Configure Streamlit page settings and styling"""
        st.set_page_config(
            page_title=self.config["page_title"],
            page_icon=self.config["page_icon"],
            layout="centered",
            initial_sidebar_state="collapsed",
        )

        # Load and apply custom CSS
        self._apply_custom_styles()

    def _apply_custom_styles(self) -> None:
        """Apply custom CSS styles to the application"""
        st.markdown(
            """
            <style>
                .stButton > button {
                    width: 100%;
                }
                .big-button {
                    height: 75px;
                    margin: 10px 0;
                }
                .progress-container {
                    margin: 20px 0;
                }
                .context-info {
                    background-color: #f0f2f6;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                /* Hide Streamlit branding */
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                /* Custom header styling */
                h1 {
                    color: #1f77b4;
                    margin-bottom: 2rem;
                }
                /* Error message styling */
                .stAlert {
                    border-radius: 4px;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )

    def init_session_state(self) -> None:
        """Initialize or reset the session state"""
        if "initialized" not in st.session_state:
            self.reset_session_state()

    def reset_session_state(self) -> None:
        """Reset all session state variables to their default values"""
        session_defaults = {
            "initialized": True,
            "step": "identify",
            "navigator": TreeNavigator(data_dir=self.config["data_dir"]),
            "error_code_step": 1,
            "current_error_code": None,
            "door_data": None,
            "history_timestamps": {},
            "show_scanner": False,
        }

        for key, value in session_defaults.items():
            st.session_state[key] = value

    def run(self) -> None:
        """Main application entry point and routing"""
        try:
            st.title("Tür Service Assistant")

            # Show analytics or main app content
            hide_main_content = show_analytics() or show_ticketing()

            if not hide_main_content:
                # Main application routing
                current_step = st.session_state.get("step", "identify")

                if current_step == "identify":
                    st.info(
                        "ℹ️ Dies ist ein interaktives Self-Service Portal für Türsysteme."
                    )
                    st.subheader(
                        "Willkommen beim Self-Service Portal! Sie haben bei Ihrer Schiebetür eine Störung festgestellt? Wir geben Ihnen praktische Hinweise, um Ihre Tür wieder in Gang zu setzen. "
                    )
                    ViewManager.show_door_identification()
                elif current_step in ["troubleshoot", "error_code_input"]:
                    ViewManager.show_troubleshooting()
                elif current_step == "end":
                    ViewManager.show_end_node()
                else:
                    logger.error(f"Invalid application step: {current_step}")
                    st.error("Ein unerwarteter Fehler ist aufgetreten.")
                    self.reset_session_state()

            # Show chat widget
            render_chat_widget()

            # Show debug information if enabled
            if self.config["debug"]:
                self._render_debug_section()

        except NavigationError as e:
            logger.error(f"Navigation error: {str(e)}")
            st.error(
                "Bei der Navigation ist ein Fehler aufgetreten. "
                "Bitte starten Sie den Prozess neu."
            )
            if st.button("Neustart"):
                self.reset_session_state()
                st.rerun()

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            st.error(str(e))

        except Exception as e:
            logger.error("Unexpected application error", exc_info=True)
            st.error(
                "Ein unerwarteter Fehler ist aufgetreten. "
                "Bitte versuchen Sie es später erneut."
            )
            if self.config["debug"]:
                st.exception(e)

    def _render_debug_section(self) -> None:
        """Render debug information for development"""
        with st.expander("Debug Information", expanded=False):
            st.write("Session State:", st.session_state)
            st.write("Configuration:", self.config)

            if st.button("Reset Session"):
                self.reset_session_state()
                st.rerun()

            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.rerun()


def create_app() -> ServiceAssistant:
    """
    Application factory function.

    Returns:
        Configured ServiceAssistant instance
    """
    return ServiceAssistant(APP_CONFIG)


def main():
    """Main entry point for the application"""
    try:
        app = create_app()
        app.run()
    except Exception as e:
        logger.critical("Failed to start application", exc_info=True)
        st.error(
            "Die Anwendung konnte nicht gestartet werden. "
            "Bitte kontaktieren Sie den Support."
        )


if __name__ == "__main__":
    main()
