"""
Employee Management Dashboard
Streamlit + SQLite  (Dashboard + Add + View + Update/Delete in one app)

Run with:  streamlit run employee_dashboard.py
"""

import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

DB_FILE = "employees.db"
DEPARTMENTS = ["HR", "Engineering", "Finance", "Sales", "Marketing", "Operations", "Other"]


# ====================== Database helpers ======================
def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_code    TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                email       TEXT,
                phone       TEXT,
                department  TEXT,
                designation TEXT,
                salary      REAL,
                join_date   TEXT
            )
            """
        )


def add_employee(emp_code, name, email, phone, department, designation, salary, join_date):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO employees
            (emp_code, name, email, phone, department, designation, salary, join_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (emp_code, name, email, phone, department, designation, salary, str(join_date)),
        )


def get_employees(search=""):
    query = "SELECT * FROM employees"
    params = ()
    if search:
        query += " WHERE name LIKE ? OR emp_code LIKE ? OR department LIKE ?"
        like = f"%{search}%"
        params = (like, like, like)
    query += " ORDER BY id DESC"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def update_employee(row_id, name, email, phone, department, designation, salary):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE employees
            SET name=?, email=?, phone=?, department=?, designation=?, salary=?
            WHERE id=?
            """,
            (name, email, phone, department, designation, salary, row_id),
        )


def delete_employee(row_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM employees WHERE id=?", (row_id,))


def load_sample_data():
    """Insert a few demo employees (skips IDs that already exist)."""
    today = date.today()
    samples = [
        ("EMP001", "Ravi Kumar", "ravi@example.com", "9000000001", "Engineering", "Software Engineer", 65000, today - timedelta(days=400)),
        ("EMP002", "Anitha Reddy", "anitha@example.com", "9000000002", "HR", "HR Executive", 42000, today - timedelta(days=300)),
        ("EMP003", "Suresh Babu", "suresh@example.com", "9000000003", "Finance", "Accountant", 48000, today - timedelta(days=220)),
        ("EMP004", "Priya Sharma", "priya@example.com", "9000000004", "Sales", "Sales Manager", 72000, today - timedelta(days=150)),
        ("EMP005", "Kiran Raju", "kiran@example.com", "9000000005", "Engineering", "Team Lead", 95000, today - timedelta(days=90)),
        ("EMP006", "Divya Lakshmi", "divya@example.com", "9000000006", "Marketing", "Designer", 46000, today - timedelta(days=45)),
        ("EMP007", "Mohan Rao", "mohan@example.com", "9000000007", "Operations", "Supervisor", 52000, today - timedelta(days=20)),
    ]
    added = 0
    for s in samples:
        try:
            add_employee(*s)
            added += 1
        except sqlite3.IntegrityError:
            pass
    return added


# ====================== Page setup ======================
st.set_page_config(page_title="Employee Dashboard", page_icon="👥", layout="wide")
init_db()

st.sidebar.title("👥 Employee Manager")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "➕ Add Employee", "📋 View Employees", "🛠️ Update / Delete"],
)
st.sidebar.divider()
if st.sidebar.button("Load sample data"):
    n = load_sample_data()
    st.sidebar.success(f"{n} sample employees added.")
st.sidebar.caption("Data is stored in a local SQLite file: employees.db")


# ====================== Dashboard ======================
if page == "📊 Dashboard":
    st.title("📊 Employee Dashboard")
    df = get_employees()

    if df.empty:
        st.info("No employee data yet. Add an employee, or click 'Load sample data' in the sidebar.")
    else:
        df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
        df["salary"] = df["salary"].fillna(0)

        # Optional department filter
        depts = sorted(df["department"].dropna().unique())
        selected = st.multiselect("Filter by department", depts, default=depts)
        view = df[df["department"].isin(selected)] if selected else df

        # ---- KPI cards ----
        month_start = pd.Timestamp(date.today().replace(day=1))
        new_this_month = int((view["join_date"] >= month_start).sum())

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Employees", len(view))
        k2.metric("Departments", view["department"].nunique())
        k3.metric("Average Salary", f"{view['salary'].mean():,.0f}")
        k4.metric("Total Payroll", f"{view['salary'].sum():,.0f}")
        k5.metric("Joined This Month", new_this_month)

        st.divider()

        # ---- Charts row 1 ----
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Employees by Department")
            st.bar_chart(view["department"].value_counts())
        with c2:
            st.subheader("Average Salary by Department")
            st.bar_chart(view.groupby("department")["salary"].mean().round(0))

        # ---- Charts row 2 ----
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Hiring Trend (per month)")
            trend = (
                view.dropna(subset=["join_date"])
                .groupby(view["join_date"].dt.to_period("M"))
                .size()
            )
            trend.index = trend.index.astype(str)
            if trend.empty:
                st.caption("No joining dates available.")
            else:
                st.line_chart(trend)
        with c4:
            st.subheader("Top 5 Highest Paid")
            top = view.nlargest(5, "salary")[["emp_code", "name", "department", "salary"]]
            st.dataframe(
                top.rename(columns={"emp_code": "ID", "name": "Name", "department": "Department", "salary": "Salary"}),
                hide_index=True,
                width="stretch",
            )

        st.subheader("Recently Added Employees")
        recent = view.sort_values("join_date", ascending=False).head(5)
        st.dataframe(
            recent[["emp_code", "name", "department", "designation", "join_date"]]
            .assign(join_date=lambda d: d["join_date"].dt.strftime("%Y-%m-%d"))
            .rename(columns={"emp_code": "ID", "name": "Name", "department": "Department",
                             "designation": "Designation", "join_date": "Joined"}),
            hide_index=True,
            width="stretch",
        )


# ====================== Add Employee ======================
elif page == "➕ Add Employee":
    st.title("➕ Add New Employee")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        emp_code = c1.text_input("Employee ID *", placeholder="EMP001")
        name = c2.text_input("Full Name *")
        email = c1.text_input("Email")
        phone = c2.text_input("Phone")
        department = c1.selectbox("Department", DEPARTMENTS)
        designation = c2.text_input("Designation")
        salary = c1.number_input("Salary", min_value=0.0, step=500.0)
        join_date = c2.date_input("Joining Date", value=date.today())
        submitted = st.form_submit_button("Save Employee", type="primary")

    if submitted:
        if not emp_code.strip() or not name.strip():
            st.error("Employee ID and Name are required.")
        else:
            try:
                add_employee(emp_code.strip(), name.strip(), email.strip(), phone.strip(),
                             department, designation.strip(), salary, join_date)
                st.success(f"Employee '{name}' added successfully.")
            except sqlite3.IntegrityError:
                st.error(f"Employee ID '{emp_code}' already exists.")


# ====================== View Employees ======================
elif page == "📋 View Employees":
    st.title("📋 Employee Records")
    search = st.text_input("Search by name, ID or department")
    df = get_employees(search)

    m1, m2 = st.columns(2)
    m1.metric("Records Found", len(df))
    m2.metric("Average Salary", f"{df['salary'].mean():,.0f}" if not df.empty else "0")

    if df.empty:
        st.info("No employees found.")
    else:
        st.dataframe(
            df.drop(columns=["id"]).rename(columns={
                "emp_code": "Employee ID", "name": "Name", "email": "Email",
                "phone": "Phone", "department": "Department",
                "designation": "Designation", "salary": "Salary", "join_date": "Joined",
            }),
            width="stretch",
            hide_index=True,
        )
        st.download_button("⬇️ Download as CSV", df.to_csv(index=False).encode("utf-8"),
                           file_name="employees.csv", mime="text/csv")


# ====================== Update / Delete ======================
elif page == "🛠️ Update / Delete":
    st.title("🛠️ Update or Delete an Employee")
    all_df = get_employees()
    if all_df.empty:
        st.info("No employees to manage yet.")
    else:
        options = {f"{r['emp_code']} – {r['name']}": r["id"] for _, r in all_df.iterrows()}
        choice = st.selectbox("Select employee", list(options.keys()))
        row = all_df[all_df["id"] == options[choice]].iloc[0]

        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            e_name = c1.text_input("Full Name", value=row["name"])
            e_email = c2.text_input("Email", value=row["email"] or "")
            e_phone = c1.text_input("Phone", value=row["phone"] or "")
            idx = DEPARTMENTS.index(row["department"]) if row["department"] in DEPARTMENTS else 0
            e_dept = c2.selectbox("Department", DEPARTMENTS, index=idx)
            e_desig = c1.text_input("Designation", value=row["designation"] or "")
            e_salary = c2.number_input("Salary", min_value=0.0, step=500.0, value=float(row["salary"] or 0))
            b1, b2 = st.columns(2)
            save = b1.form_submit_button("Update", type="primary")
            remove = b2.form_submit_button("Delete")

        if save:
            update_employee(int(row["id"]), e_name, e_email, e_phone, e_dept, e_desig, e_salary)
            st.success("Employee updated.")
        if remove:
            delete_employee(int(row["id"]))
            st.warning("Employee deleted. Select another page or refresh to update the list.")
