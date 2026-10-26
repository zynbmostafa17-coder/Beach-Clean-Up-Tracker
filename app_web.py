import sqlite3
from pathlib import Path
from datetime import date, datetime

import streamlit as st

st.set_page_config(
    page_title="Beach Clean-Up Tracker",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).with_name("beach_cleanup_data.db")

# ---------- Theme ----------
st.markdown("""
<style>
:root { --navy:#123B4A; --teal:#168C86; --mint:#DDF2ED; --bg:#F2F8F7; }
.stApp { background: linear-gradient(180deg,#F4FAF9 0%,#FFFFFF 55%,#F2F8F7 100%); }
.block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1400px; }
.hero {
  background: linear-gradient(115deg,#123B4A 0%,#167D7A 65%,#28A99B 100%);
  padding: 1.6rem 1.7rem; border-radius: 22px; color: white; margin-bottom: 1.2rem;
  box-shadow: 0 12px 30px rgba(18,59,74,.13);
}
.hero h1 { color:white; font-size: clamp(1.7rem, 4vw, 2.45rem); margin:0 0 .35rem 0; }
.hero p { color:#D9F3EF; margin:0; font-size:1rem; }
.metric-card {
  background:#FFFFFF; border:1px solid #D8E8E5; border-radius:18px;
  padding:1rem 1.1rem; min-height:112px; box-shadow:0 5px 18px rgba(18,59,74,.045);
}
.metric-label { color:#668087; font-size:.78rem; font-weight:700; letter-spacing:.045em; text-transform:uppercase; }
.metric-value { color:#168C86; font-size:2rem; font-weight:800; line-height:1.3; }
.metric-note { color:#668087; font-size:.82rem; }
.section-title { color:#123B4A; font-weight:800; font-size:1.25rem; margin:.3rem 0 .7rem 0; }
.beach-card {
  background:#FFFFFF; border:1px solid #D8E8E5; border-radius:16px;
  padding:1rem 1.1rem; margin-bottom:.75rem;
}
.small-muted { color:#668087; font-size:.88rem; }
div[data-testid="stMetric"] {
  background:#fff; border:1px solid #D8E8E5; border-radius:16px; padding:1rem;
}
div[data-testid="stMetricLabel"] { color:#668087; }
div[data-testid="stMetricValue"] { color:#168C86; }
.stButton button[kind="primary"] { background:#168C86; border-color:#168C86; }
.stButton button { border-radius:10px; }
[data-testid="stSidebar"] { background:#EAF5F2; }
@media (max-width: 700px) {
  .block-container { padding-left: .8rem; padding-right: .8rem; }
  .hero { padding:1.25rem; border-radius:16px; }
}
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS beaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT DEFAULT '',
            bin_type TEXT DEFAULT 'Trash bin',
            distance TEXT DEFAULT '',
            status TEXT DEFAULT 'Needs Cleaning',
            notes TEXT DEFAULT ''
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS cleanups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beach_id INTEGER,
            cleanup_date TEXT NOT NULL,
            volunteers INTEGER DEFAULT 0,
            bags_collected INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            FOREIGN KEY(beach_id) REFERENCES beaches(id) ON DELETE SET NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )""")
        # Add columns if an older version of the web database is reused.
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(beaches)").fetchall()}
        if "bin_type" not in cols:
            conn.execute("ALTER TABLE beaches ADD COLUMN bin_type TEXT DEFAULT 'Trash bin'")
        if "distance" not in cols:
            conn.execute("ALTER TABLE beaches ADD COLUMN distance TEXT DEFAULT ''")
        existing = conn.execute("SELECT COUNT(*) FROM beaches").fetchone()[0]
        if existing == 0:
            samples = [
                ("Al-Salam Beach", "Suez", "Recycling + Trash", "0.4 km", "Clean", "Recently checked"),
                ("Port Tawfiq Beach", "Suez", "Trash bin", "1.2 km", "Needs Cleaning", "Litter reported"),
                ("Ain Sokhna Beach", "Ain Sokhna", "Recycling bin", "8.5 km", "Fair", "Some litter found"),
                ("Adabiya Coast", "Suez", "Trash bin", "5.0 km", "Clean", "No recent reports"),
                ("Moussa Bay", "Ain Sokhna", "Recycling + Trash", "12 km", "Fair", "Check again soon"),
            ]
            conn.executemany(
                "INSERT INTO beaches(name,location,bin_type,distance,status,notes) VALUES(?,?,?,?,?,?)",
                samples,
            )
        conn.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES('reminder',?)",
            ("Join a beach clean-up this weekend!",),
        )

init_db()

def get_setting(key, default=""):
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(key, value):
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>🌊 Beach Clean-Up Tracker</h1>
  <p>Find beach locations · Track cleanliness · Record clean-ups · Protect our coast</p>
</div>
""", unsafe_allow_html=True)

with connect() as conn:
    beach_count = conn.execute("SELECT COUNT(*) FROM beaches").fetchone()[0]
    clean_count = conn.execute("SELECT COUNT(*) FROM beaches WHERE status='Clean'").fetchone()[0]
    event_count = conn.execute("SELECT COUNT(*) FROM cleanups").fetchone()[0]
    total_bags = conn.execute("SELECT COALESCE(SUM(bags_collected),0) FROM cleanups").fetchone()[0]
    total_volunteers = conn.execute("SELECT COALESCE(SUM(volunteers),0) FROM cleanups").fetchone()[0]

m1, m2, m3, m4 = st.columns(4)
for col, label, value, note in [
    (m1, "Beach locations", beach_count, "Locations being tracked"),
    (m2, "Clean beaches", clean_count, f"Out of {beach_count} locations"),
    (m3, "Clean-up sessions", event_count, "Events recorded"),
    (m4, "Bags collected", total_bags, f"{total_volunteers} volunteer attendances"),
]:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
page = st.radio(
    "Navigation",
    ["🏝️ Beaches", "🧹 Record a clean-up", "📊 Reports", "🔔 Reminder"],
    horizontal=True,
    label_visibility="collapsed",
)

STATUS_OPTIONS = ["Clean", "Fair", "Needs Cleaning"]
STATUS_EMOJI = {"Clean": "🟢", "Fair": "🟡", "Needs Cleaning": "🔴"}

# ---------- Beaches ----------
if page == "🏝️ Beaches":
    st.markdown('<div class="section-title">Explore beach locations</div>', unsafe_allow_html=True)
    with st.expander("＋ Add a new beach", expanded=False):
        with st.form("add_beach", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Beach name *", placeholder="e.g. New Beach")
            area = b.text_input("Area / city", placeholder="e.g. Suez")
            c, d = st.columns(2)
            bin_type = c.selectbox("Bin type", ["Recycling + Trash", "Recycling bin", "Trash bin", "No bin information"])
            status = d.selectbox("Cleanliness status", STATUS_OPTIONS, index=2)
            notes = st.text_area("Notes", placeholder="Any observations about this beach")
            submitted = st.form_submit_button("Add beach", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Please enter a beach name.")
                else:
                    try:
                        with connect() as conn:
                            conn.execute(
                                "INSERT INTO beaches(name,location,bin_type,status,notes) VALUES(?,?,?,?,?)",
                                (name.strip(), area.strip(), bin_type, status, notes.strip()),
                            )
                        st.success("Beach added successfully.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("A beach with that name already exists.")

    f1, f2 = st.columns([2, 1])
    term = f1.text_input("🔎 Search beaches", placeholder="Search by beach, area, bin type, or status")
    chosen_status = f2.selectbox("Filter by status", ["All statuses"] + STATUS_OPTIONS)
    with connect() as conn:
        all_beaches = conn.execute("SELECT * FROM beaches ORDER BY name").fetchall()
    beaches = []
    for beach in all_beaches:
        haystack = f"{beach['name']} {beach['location']} {beach['bin_type']} {beach['status']} {beach['notes']}".lower()
        if term.lower().strip() and term.lower().strip() not in haystack:
            continue
        if chosen_status != "All statuses" and beach["status"] != chosen_status:
            continue
        beaches.append(beach)

    st.caption(f"Showing {len(beaches)} of {len(all_beaches)} beach locations")
    if not beaches:
        st.info("No beaches match your search. Try another keyword or add a new beach.")
    for beach in beaches:
        with st.container(border=True):
            head, status_col = st.columns([3, 1])
            head.markdown(f"### 🏖️ {beach['name']}")
            status_col.markdown(f"**{STATUS_EMOJI.get(beach['status'], '⚪')} {beach['status']}**")
            st.markdown(
                f"📍 **Area:** {beach['location'] or 'Not specified'} &nbsp;&nbsp; "
                f"♻️ **Bins:** {beach['bin_type'] or 'Not specified'} &nbsp;&nbsp; "
                f"📏 **Example distance:** {beach['distance'] or 'Not available'}",
                unsafe_allow_html=True,
            )
            st.caption(beach["notes"] or "No notes added yet.")
            with st.expander("View details and update status"):
                new_status = st.selectbox(
                    "Cleanliness status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(beach["status"]) if beach["status"] in STATUS_OPTIONS else 2,
                    key=f"status_{beach['id']}",
                )
                new_notes = st.text_area("Notes", value=beach["notes"] or "", key=f"notes_{beach['id']}")
                x, y = st.columns(2)
                if x.button("Save changes", key=f"save_{beach['id']}", type="primary", use_container_width=True):
                    with connect() as conn:
                        conn.execute(
                            "UPDATE beaches SET status=?, notes=? WHERE id=?",
                            (new_status, new_notes.strip(), beach["id"]),
                        )
                    st.success("Beach details updated.")
                    st.rerun()
                if y.button("Delete beach", key=f"delete_{beach['id']}", use_container_width=True):
                    st.session_state["confirm_delete_beach"] = beach["id"]
                if st.session_state.get("confirm_delete_beach") == beach["id"]:
                    st.warning("Are you sure? This removes the beach and unlinks its clean-up records.")
                    yes, no = st.columns(2)
                    if yes.button("Yes, delete", key=f"yes_delete_{beach['id']}"):
                        with connect() as conn:
                            conn.execute("DELETE FROM beaches WHERE id=?", (beach["id"],))
                        st.session_state.pop("confirm_delete_beach", None)
                        st.rerun()
                    if no.button("Cancel", key=f"no_delete_{beach['id']}"):
                        st.session_state.pop("confirm_delete_beach", None)
                        st.rerun()

# ---------- Record a clean-up ----------
elif page == "🧹 Record a clean-up":
    st.markdown('<div class="section-title">Record a clean-up event</div>', unsafe_allow_html=True)
    with connect() as conn:
        beaches = conn.execute("SELECT id,name FROM beaches ORDER BY name").fetchall()
    if not beaches:
        st.info("Add a beach first in the Beaches section.")
    else:
        beach_map = {b["name"]: b["id"] for b in beaches}
        with st.container(border=True):
            with st.form("record_cleanup", clear_on_submit=True):
                selected_name = st.selectbox("Beach", list(beach_map.keys()))
                a, b = st.columns(2)
                cleanup_date = a.date_input("Date of clean-up", value=date.today())
                volunteers = b.number_input("Number of volunteers", min_value=0, max_value=100000, value=1, step=1)
                bags = st.number_input("Bags of rubbish collected", min_value=0, max_value=1000000, value=1, step=1)
                notes = st.text_area("Notes / observations", placeholder="What happened during the clean-up?")
                saved = st.form_submit_button("Save clean-up session", type="primary", use_container_width=True)
                if saved:
                    with connect() as conn:
                        conn.execute(
                            "INSERT INTO cleanups(beach_id,cleanup_date,volunteers,bags_collected,notes) VALUES(?,?,?,?,?)",
                            (beach_map[selected_name], cleanup_date.isoformat(), int(volunteers), int(bags), notes.strip()),
                        )
                    st.success(f"Clean-up saved for {selected_name}. Great work! 🌱")
                    st.rerun()

# ---------- Reports ----------
elif page == "📊 Reports":
    st.markdown('<div class="section-title">Environmental impact reports</div>', unsafe_allow_html=True)
    with connect() as conn:
        rows = conn.execute("""
            SELECT c.id, c.cleanup_date, COALESCE(b.name,'Deleted beach') AS beach,
                   c.volunteers, c.bags_collected, c.notes
            FROM cleanups c LEFT JOIN beaches b ON b.id=c.beach_id
            ORDER BY c.cleanup_date DESC, c.id DESC
        """).fetchall()
        by_beach = conn.execute("""
            SELECT COALESCE(b.name,'Deleted beach') AS beach,
                   SUM(c.bags_collected) AS bags,
                   SUM(c.volunteers) AS volunteers,
                   COUNT(c.id) AS sessions
            FROM cleanups c LEFT JOIN beaches b ON b.id=c.beach_id
            GROUP BY beach ORDER BY bags DESC
        """).fetchall()
    if rows:
        chart_rows = [dict(r) for r in by_beach]
        if chart_rows:
            st.markdown("#### Bags collected by beach")
            st.bar_chart({r["beach"]: r["bags"] or 0 for r in chart_rows})
        st.markdown("#### Clean-up history")
        st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
        csv = "Date,Beach,Volunteers,Bags collected,Notes\n" + "\n".join(
            ",".join('"' + str(value if value is not None else "").replace('"', '""') + '"' for value in [
                r["cleanup_date"], r["beach"], r["volunteers"], r["bags_collected"], r["notes"]
            ]) for r in rows
        )
        st.download_button("⬇️ Download report as CSV", csv, file_name="beach_cleanup_report.csv", mime="text/csv")
    else:
        st.info("No clean-up sessions recorded yet. Record your first clean-up to see reports here.")

# ---------- Reminder ----------
elif page == "🔔 Reminder":
    st.markdown('<div class="section-title">Your clean-up reminder</div>', unsafe_allow_html=True)
    reminder = get_setting("reminder", "Join a beach clean-up this weekend!")
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">CURRENT REMINDER</div>'
        f'<div style="font-size:1.15rem;color:#123B4A;font-weight:650;margin-top:.55rem;">♻️ {reminder}</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("reminder_form"):
        new_reminder = st.text_area("Edit reminder message", value=reminder, max_chars=300)
        save_reminder = st.form_submit_button("Save reminder", type="primary", use_container_width=True)
        if save_reminder:
            if not new_reminder.strip():
                st.error("Please enter a reminder message.")
            else:
                set_setting("reminder", new_reminder.strip())
                st.success("Reminder saved.")
                st.rerun()

st.divider()
st.caption("Beach Clean-Up Tracker · Demo project · Sample distances only — no live GPS or online notifications.")
st.caption("Data note: this version uses a SQLite file beside the app. Streamlit Community Cloud storage may not be permanent; connect a hosted database before relying on it for long-term or multi-user records.")
