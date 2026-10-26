import streamlit as st
import sqlite3
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Beach Clean-Up Tracker", page_icon="🏖️", layout="wide")

DB_PATH = Path(__file__).with_name("beach_cleanup_data.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS beaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT DEFAULT '',
            status TEXT DEFAULT 'Needs cleaning',
            notes TEXT DEFAULT ''
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS cleanups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beach_id INTEGER,
            cleanup_date TEXT NOT NULL,
            volunteers INTEGER DEFAULT 0,
            bags_collected INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            FOREIGN KEY(beach_id) REFERENCES beaches(id)
        )""")

init_db()

st.title("🏖️ Beach Clean-Up Tracker")
st.caption("Track beaches, record clean-up activities, and see your impact.")

with connect() as conn:
    beach_count = conn.execute("SELECT COUNT(*) FROM beaches").fetchone()[0]
    cleanup_count = conn.execute("SELECT COUNT(*) FROM cleanups").fetchone()[0]
    total_bags = conn.execute("SELECT COALESCE(SUM(bags_collected),0) FROM cleanups").fetchone()[0]
    total_volunteers = conn.execute("SELECT COALESCE(SUM(volunteers),0) FROM cleanups").fetchone()[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Beaches tracked", beach_count)
c2.metric("Clean-up events", cleanup_count)
c3.metric("Bags collected", total_bags)
c4.metric("Volunteer attendances", total_volunteers)

tab1, tab2, tab3 = st.tabs(["🏝️ Beaches", "🧹 Record a clean-up", "📊 Reports"])

with tab1:
    st.subheader("Beach directory")
    with st.form("add_beach", clear_on_submit=True):
        name = st.text_input("Beach name *")
        location = st.text_input("Location / area")
        status = st.selectbox("Current status", ["Needs cleaning", "In progress", "Clean"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add beach")
        if submitted:
            if not name.strip():
                st.error("Please enter a beach name.")
            else:
                with connect() as conn:
                    conn.execute(
                        "INSERT INTO beaches(name, location, status, notes) VALUES(?,?,?,?)",
                        (name.strip(), location.strip(), status, notes.strip())
                    )
                st.success("Beach added.")
                st.rerun()

    with connect() as conn:
        beaches = conn.execute("SELECT * FROM beaches ORDER BY name").fetchall()
    if beaches:
        for b in beaches:
            with st.expander(f"{b['name']} — {b['status']}"):
                st.write("**Location:**", b["location"] or "Not specified")
                st.write("**Notes:**", b["notes"] or "None")
                new_status = st.selectbox(
                    "Update status", ["Needs cleaning", "In progress", "Clean"],
                    index=["Needs cleaning", "In progress", "Clean"].index(b["status"]),
                    key=f"status_{b['id']}"
                )
                col_a, col_b = st.columns(2)
                if col_a.button("Save status", key=f"save_{b['id']}"):
                    with connect() as conn:
                        conn.execute("UPDATE beaches SET status=? WHERE id=?", (new_status, b["id"]))
                    st.success("Status updated.")
                    st.rerun()
                if col_b.button("Delete beach", key=f"delete_{b['id']}"):
                    with connect() as conn:
                        conn.execute("DELETE FROM cleanups WHERE beach_id=?", (b["id"],))
                        conn.execute("DELETE FROM beaches WHERE id=?", (b["id"],))
                    st.rerun()
    else:
        st.info("No beaches yet. Add your first beach using the form above.")

with tab2:
    st.subheader("Record a clean-up event")
    with connect() as conn:
        beaches = conn.execute("SELECT id, name FROM beaches ORDER BY name").fetchall()
    if not beaches:
        st.info("Add a beach in the Beaches tab before recording a clean-up.")
    else:
        labels = {f"{b['name']} (ID {b['id']})": b['id'] for b in beaches}
        with st.form("add_cleanup", clear_on_submit=True):
            selected = st.selectbox("Beach", list(labels.keys()))
            cleanup_date = st.date_input("Date", value=date.today())
            volunteers = st.number_input("Number of volunteers", min_value=0, step=1)
            bags = st.number_input("Bags of rubbish collected", min_value=0, step=1)
            notes = st.text_area("Notes / observations")
            submitted = st.form_submit_button("Save clean-up")
            if submitted:
                with connect() as conn:
                    conn.execute(
                        "INSERT INTO cleanups(beach_id, cleanup_date, volunteers, bags_collected, notes) VALUES(?,?,?,?,?)",
                        (labels[selected], cleanup_date.isoformat(), int(volunteers), int(bags), notes.strip())
                    )
                st.success("Clean-up event saved.")
                st.rerun()

with tab3:
    st.subheader("Clean-up history")
    with connect() as conn:
        rows = conn.execute("""
            SELECT c.cleanup_date, b.name AS beach, c.volunteers, c.bags_collected, c.notes
            FROM cleanups c LEFT JOIN beaches b ON b.id = c.beach_id
            ORDER BY c.cleanup_date DESC, c.id DESC
        """).fetchall()
    if rows:
        st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
    else:
        st.info("No clean-up events recorded yet.")

st.divider()
st.caption("Demo note: this first version stores data in a local SQLite file. For reliable shared online data across phones and computers, connect a hosted database before using it with multiple people.")
