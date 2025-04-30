import os
import time
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from service.database.models import ServiceTicket
from service.database.database import get_db


class TicketingDashboard:
    """Ticketing dashboard for TSB door service"""

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    TICKET_STATUSES = ["open", "assigned", "completed"]

    @staticmethod
    def render_login():
        """Render the login form for ticketing access"""
        st.subheader("Ticket System Login")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if password == TicketingDashboard.ADMIN_PASSWORD:
                st.session_state.ticketing_authenticated = True
                st.rerun()
            else:
                st.error("Invalid password")

    @staticmethod
    def get_tickets(db: Session) -> pd.DataFrame:
        """Fetch all tickets and convert to DataFrame"""
        tickets = db.query(ServiceTicket).all()

        ticket_data = []
        for ticket in tickets:
            history = ticket.troubleshooting_history
            ticket_data.append(
                {
                    "ID": ticket.id,
                    "Created": ticket.created_at,
                    "Status": ticket.status,
                    "Priority": ticket.priority,
                    "Contact": ticket.contact_name,
                    "Door": history.door_serial,
                    "Type": history.door_type,
                    "Assigned To": ticket.assigned_to or "-",
                    "Last Updated": ticket.last_updated or ticket.created_at,
                }
            )

        df = pd.DataFrame(ticket_data)
        if not df.empty:
            df["Created"] = pd.to_datetime(df["Created"]).dt.strftime("%Y-%m-%d %H:%M")
            df["Last Updated"] = pd.to_datetime(df["Last Updated"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )

        return df

    @staticmethod
    def update_ticket(
        db: Session, ticket_id: int, status: str, assigned_to: Optional[str] = None
    ):
        """Update ticket status and assignment"""
        ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            if assigned_to:
                ticket.assigned_to = assigned_to
            ticket.last_updated = datetime.now(pytz.timezone("Europe/Berlin"))
            db.commit()
            return True
        return False

    @staticmethod
    def render_ticket_details(db: Session, ticket_id: int):
        """Render detailed view of a single ticket"""
        ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
        if not ticket:
            st.error("Ticket not found")
            return

        st.subheader(f"Ticket #{ticket.id}")

        # Create two columns for main info and actions
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("### Door Information")
            history = ticket.troubleshooting_history
            st.info(f"Door Serial: {history.door_serial}")
            st.info(f"Door Type: {history.door_type}")

            st.write("### Contact Information")
            st.write(f"Name: {ticket.contact_name}")
            st.write(f"Phone: {ticket.contact_phone}")
            st.write(f"Email: {ticket.contact_email}")

            if ticket.additional_info:
                st.write("### Additional Information")
                st.text_area("Notes", ticket.additional_info, disabled=True)

            st.write("### Troubleshooting History")
            for step in history.history_steps:
                st.write(f"- {step['timestamp']}: {step['node_text']}")

        with col2:
            st.write("### Ticket Actions")

            new_status = st.selectbox(
                "Status",
                options=TicketingDashboard.TICKET_STATUSES,
                index=TicketingDashboard.TICKET_STATUSES.index(ticket.status),
            )

            new_assignment = st.text_input(
                "Assign to (email)", value=ticket.assigned_to or ""
            )

            if st.button("Update Ticket"):
                try:
                    if TicketingDashboard.update_ticket(
                        db, ticket.id, new_status, new_assignment
                    ):
                        st.toast(f"Ticket #{ticket.id} updated successfully", icon="✅")
                        time.sleep(1)  # Small delay to ensure toast is visible
                        st.rerun()
                    else:
                        st.toast(f"Failed to update ticket #{ticket.id}", icon="❌")
                except Exception as e:
                    st.toast(f"Error updating ticket: {str(e)}", icon="❌")

    @staticmethod
    def render_dashboard():
        """Render the main ticketing dashboard"""
        st.title("TSB Service Ticketing")

        db = next(get_db())
        tickets_df = TicketingDashboard.get_tickets(db)

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=TicketingDashboard.TICKET_STATUSES,
                default=TicketingDashboard.TICKET_STATUSES,
            )
        with col2:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=tickets_df["Priority"].unique().tolist(),
                default=tickets_df["Priority"].unique().tolist(),
            )

        # Apply filters
        filtered_df = tickets_df[
            tickets_df["Status"].isin(status_filter)
            & tickets_df["Priority"].isin(priority_filter)
        ]

        # Show tickets table
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small"),
                    "Created": st.column_config.DatetimeColumn(
                        "Created", width="medium"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        width="small",
                        options=TicketingDashboard.TICKET_STATUSES,
                    ),
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                },
                hide_index=True,
            )

            # Manual ticket selection
            ticket_id = st.number_input("Enter ticket ID to view details", min_value=1)
            if st.button("View Ticket"):
                st.session_state.selected_ticket = ticket_id
                st.rerun()
        else:
            st.info("No tickets found matching the filters")

        # Show selected ticket details
        if "selected_ticket" in st.session_state:
            st.markdown("---")
            TicketingDashboard.render_ticket_details(
                db, st.session_state.selected_ticket
            )


def show_ticketing():
    """Main entry point for ticketing functionality"""
    if "ticketing_authenticated" not in st.session_state:
        st.session_state.ticketing_authenticated = False

    # Sidebar button
    with st.sidebar:
        if not st.session_state.ticketing_authenticated:
            if st.button("🎫 Ticket System"):
                st.session_state.show_ticketing_login = True
                st.rerun()

        if st.session_state.get("show_ticketing_login", False):
            TicketingDashboard.render_login()

    # Main content area
    if st.session_state.ticketing_authenticated:
        # Back button
        if st.button("← Zurück zur Hauptseite"):
            st.session_state.ticketing_authenticated = False
            st.session_state.show_ticketing_login = False
            st.rerun()

        TicketingDashboard.render_dashboard()
        return True

    return False
