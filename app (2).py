"""
Employee Management - Talent Management Platform
Run with:  streamlit run app.py
"""

import sqlite3

import pandas as pd
import streamlit as st

DB_NAME = "employees.db"


# ---------- Database helpers ----------
def get_connection():
    """Open a connection to the SQLite database file."""
    return sqlite3.connect(DB_NAME)


def create_table():
    """Create the employees table if it does not exist yet."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            role       TEXT NOT NULL,
            join_date  TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_employee(name, email, department, role, join_date):
    """Insert a new employee. Returns True on success, False if email exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO employees (name, email, department, role, join_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, email, department, role, str(join_date)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_all_employees():
    """Return all employees as a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY id", conn)
    conn.close()
    return df


# ---------- Streamlit user interface ----------
create_table()

st.title("👥 Employee Management")
st.caption("Talent Management Platform")

tab_add, tab_view = st.tabs(["➕ Add Employee", "📋 View Employees"])

with tab_add:
    st.subheader("Add a new employee")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        department = st.selectbox(
            "Department", ["Engineering", "HR", "Finance", "Marketing", "Sales", "Other"]
        )
        role = st.text_input("Job role")
        join_date = st.date_input("Joining date")
        submitted = st.form_submit_button("Save employee")

    if submitted:
        if not name.strip() or not email.strip() or not role.strip():
            st.error("Please fill in name, email, and role.")
        elif "@" not in email:
            st.error("Please enter a valid email address.")
        elif add_employee(name.strip(), email.strip(), department, role.strip(), join_date):
            st.success(f"{name} was added successfully!")
        else:
            st.error("An employee with this email already exists.")

with tab_view:
    st.subheader("Saved employees")
    employees = get_all_employees()
    if employees.empty:
        st.info("No employees yet. Add one in the first tab.")
    else:
        st.dataframe(employees, use_container_width=True, hide_index=True)
        st.write(f"Total employees: **{len(employees)}**")
