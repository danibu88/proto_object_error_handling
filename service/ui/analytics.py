# tsb_door_service/ui/analytics.py

import os
import streamlit as st
import pandas as pd
import pytz
from typing import Dict, List, Any
from collections import Counter
from sqlalchemy.orm import Session

from service.database.models import TroubleshootingHistory, ServiceTicket
from service.database.database import get_db


class AnalyticsDashboard:
    """Analytics dashboard for TSB door service"""

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    @staticmethod
    def show_analytics_button():
        """Display the analytics access button"""
        if st.button("📊 Analytics Dashboard"):
            st.session_state.show_analytics_login = True

    @staticmethod
    def render_login():
        """Render the login form for analytics access"""
        st.subheader("Analytics Login")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if password == AnalyticsDashboard.ADMIN_PASSWORD:
                st.session_state.analytics_authenticated = True
                st.rerun()
            else:
                st.error("Invalid password")

    @staticmethod
    def get_analytics_data(db: Session) -> Dict[str, Any]:
        """Fetch and process analytics data"""
        from datetime import timedelta, datetime

        # Get current date and last week's date
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        week_ago = now - timedelta(days=7)

        # Get all histories and last week's histories
        all_histories = db.query(TroubleshootingHistory).all()
        current_histories = (
            db.query(TroubleshootingHistory)
            .filter(TroubleshootingHistory.start_time >= week_ago)
            .all()
        )
        previous_histories = (
            db.query(TroubleshootingHistory)
            .filter(TroubleshootingHistory.start_time < week_ago)
            .all()
        )

        # Calculate current metrics
        total_processes = len(all_histories)
        current_total = len(current_histories)
        previous_total = len(previous_histories)

        # Calculate ratios for current week
        current_solved = sum(
            1 for h in current_histories if h.final_node == "problem_solved"
        )
        current_service = sum(
            1 for h in current_histories if h.final_node == "service_required"
        )
        current_not_supported = sum(
            1 for h in current_histories if h.final_node == "not_supported"
        )
        current_solved_ratio = (
            (current_solved / current_total) if current_total > 0 else 0
        )
        current_service_ratio = (
            (current_service / current_total) if current_total > 0 else 0
        )
        current_not_supported_ratio = (
            (current_not_supported / current_total) if current_total > 0 else 0
        )

        # Calculate ratios for previous week
        previous_solved = sum(
            1 for h in previous_histories if h.final_node == "problem_solved"
        )
        previous_service = sum(
            1 for h in previous_histories if h.final_node == "service_required"
        )
        previous_solved_ratio = (
            (previous_solved / previous_total) if previous_total > 0 else 0
        )
        previous_service_ratio = (
            (previous_service / previous_total) if previous_total > 0 else 0
        )
        previous_not_supported_ratio = (
            (current_not_supported / previous_total) if previous_total > 0 else 0
        )

        # Calculate deltas
        total_delta = current_total - previous_total
        solved_ratio_delta = current_solved_ratio - previous_solved_ratio
        service_ratio_delta = current_service_ratio - previous_service_ratio
        not_supported_delta = current_not_supported_ratio - previous_not_supported_ratio

        # Calculate average duration
        durations = []
        for history in all_histories:
            duration = (history.end_time - history.start_time).total_seconds() / 60
            durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Analyze top cases
        def _generate_path_id(history: List[Dict]) -> str:
            """Convert sequence of steps into path identifier."""
            return "->".join(step.get("id", step["node_text"]) for step in history)

        # Replace the steps analysis section
        solved_paths = []
        service_paths = []

        for history in all_histories:
            path = _generate_path_id(history.history_steps)
            # handle empty path due to empty history
            path = "not_supported" if path == "" else path
            if history.final_node == "problem_solved":
                solved_paths.append(path)
            else:
                service_paths.append(path)

        top_solved = Counter(solved_paths).most_common(3)
        top_service = Counter(service_paths).most_common(3)

        return {
            "all_histories": all_histories,
            "total_processes": total_processes,
            "total_delta": total_delta,
            "solved_ratio": current_solved_ratio,
            "solved_ratio_delta": solved_ratio_delta,
            "service_ratio": current_service_ratio,
            "service_ratio_delta": service_ratio_delta,
            "non_supported_ratio": current_not_supported_ratio,
            "not_supported_delta": not_supported_delta,
            "avg_duration": avg_duration,
            "top_solved": top_solved,
            "top_service": top_service,
        }

    @staticmethod
    def render_dashboard():
        """Render the analytics dashboard"""
        st.title("TSB Service Analytics")

        db = next(get_db())
        data = AnalyticsDashboard.get_analytics_data(db)

        # Overview metrics
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        col1.metric(
            "Gesamtanzahl Prozesse",
            data["total_processes"],
            delta=data["total_delta"],
            border=True,
            help="Anzahl der durchgeführten Troubleshooting-Prozesse und Veränderung zur Vorwoche",
        )
        col2.metric(
            "Gelöste Fälle Anteil letzte Woche",
            f"{data['solved_ratio']:.1%}",
            delta=f"{data['solved_ratio_delta']:.1%}",
            border=True,
            help="Anteil der gelösten Fälle an allen Prozessen und Veränderung zur Vorwoche",
        )

        col3.metric(
            "Anteil Service angefordert letzte Woche",
            f"{data['service_ratio']:.1%}",
            delta=f"{data['service_ratio_delta']:.1%}",
            border=True,
            help="Anteil der Service-Ticket-Anfragen an allen Prozessen und Veränderung zur Vorwoche",
        )
        col4.metric(
            "Anteil nicht unterstützte Fälle letzte Woche",
            f"{data['non_supported_ratio']:.1%}",
            delta=f"{data['not_supported_delta']:.1%}",
            border=True,
            help="Anteil der nicht unterstützten Fälle an allen Prozessen und Veränderung zur Vorwoche",
        )

        st.info(
            f"⏰ Durchschnittliche Bearbeitungsdauer: **{data['avg_duration']:.1f} Minuten**"
        )

        st.subheader("Top 3 gelöste Fälle")
        solved_df = pd.DataFrame(
            data["top_solved"], columns=["Fallbeschreibung", "Anzahl"]
        )
        st.table(solved_df)

        st.subheader("Top 3 Service-Ticket Fälle")
        service_df = pd.DataFrame(
            data["top_service"], columns=["Fallbeschreibung", "Anzahl"]
        )
        st.table(service_df)

        # Additional visualizations
        histories = pd.DataFrame(
            [
                {
                    "datetime": pd.to_datetime(h.start_time),  # Ensure proper datetime
                    "type": (
                        "Gelöst"
                        if h.final_node == "problem_solved"
                        else "Service angefordert"
                    ),
                }
                for h in data["all_histories"]
            ]
        )

        if not histories.empty:
            # Group by hour and type
            chart_data = (
                histories.set_index("datetime")
                .groupby([pd.Grouper(freq="h"), "type"])
                .size()
                .unstack(fill_value=0)
            )

            st.subheader("Anzahl Fälle pro Stunde")
            st.bar_chart(
                chart_data, color=["#228100", "#fd0"], x_label="Zeit", y_label="Anzahl"
            )


def show_analytics():
    """Main entry point for analytics functionality"""
    # Initialize session states
    if "analytics_authenticated" not in st.session_state:
        st.session_state.analytics_authenticated = False
    if "show_analytics_login" not in st.session_state:
        st.session_state.show_analytics_login = False

    # Sidebar login
    with st.sidebar:
        if not st.session_state.analytics_authenticated:
            if not st.session_state.show_analytics_login:
                if st.button("📊 Analytics Dashboard"):
                    st.session_state.show_analytics_login = True
                    st.rerun()
            else:
                st.subheader("Analytics Login")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if password == AnalyticsDashboard.ADMIN_PASSWORD:
                        st.session_state.analytics_authenticated = True
                        st.rerun()
                    else:
                        st.error("👀 Invalid password")

    # Main content area
    if st.session_state.analytics_authenticated:
        # Back button
        if st.button("← Zurück zur Hauptseite"):
            st.session_state.analytics_authenticated = False
            st.session_state.show_analytics_login = False
            st.rerun()

        # Show analytics dashboard
        AnalyticsDashboard.render_dashboard()
        return True  # Signal to main app to hide other content

    return False  # Signal to main app to show normal content
