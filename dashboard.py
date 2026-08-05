import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta

FILE = "CHILD_Decode_Tracker.xlsx"

# How many days before the decode date the daily reminder window opens.
REMINDER_WINDOW_DAYS = 7

# -----------------------------------
# Page Configuration
# -----------------------------------

st.set_page_config(
    page_title="CHILD Decode Management",
    page_icon="🧬",
    layout="wide"
)

# -----------------------------------
# Styling
# -----------------------------------

st.markdown(
    """
    <style>

    .main {
        background-color:#f8fafc;
    }

    .header {
        background-color:#0f766e;
        padding:20px;
        border-radius:12px;
        color:white;
        margin-bottom:20px;
    }

    .card {
        background:white;
        padding:15px;
        border-radius:10px;
        border:1px solid #e5e7eb;
        text-align:center;
    }

    .card-title {
        font-size:14px;
        color:#64748b;
    }

    .card-value {
        font-size:30px;
        font-weight:bold;
        color:#0f172a;
    }

    .reminder-banner {
        background-color:#fef3c7;
        border:1px solid #f59e0b;
        border-radius:10px;
        padding:15px;
        margin-bottom:15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# Calendar-based Decode Date Logic
# -----------------------------------

def last_saturday(year, month):
    """Return the last Saturday of the given month/year as a Timestamp."""
    last_day = calendar.monthrange(year, month)[1]
    date = datetime(year, month, last_day)
    while date.weekday() != 5:  # 5 = Saturday
        date -= timedelta(days=1)
    return pd.Timestamp(date)

def decode_date_for_period(year, month):
    return last_saturday(year, month)

def get_next_decode(today=None):
    """Find the next upcoming decode date (this month or a future month)."""
    today = today or pd.Timestamp.today().normalize()
    current_year = today.year
    current_month = today.month

    for month_offset in range(0, 13):
        month = current_month + month_offset
        year = current_year
        while month > 12:
            month -= 12
            year += 1
        decode_date = decode_date_for_period(year, month)
        if decode_date >= today:
            return decode_date

def build_decode_calendar(months_back=1, months_ahead=18, today=None):
    """
    Build a table of {DECODE MONTH, DATE} purely from the calendar rule
    (last Saturday of each month).
    """
    today = today or pd.Timestamp.today().normalize()
    rows = []

    for offset in range(-months_back, months_ahead):
        month = today.month + offset
        year = today.year
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        decode_date = decode_date_for_period(year, month)
        rows.append({
            "DECODE MONTH": decode_date.strftime("%B %Y"),
            "DATE": decode_date
        })

    return pd.DataFrame(rows)

def in_reminder_window(decode_date, today):
    """True if today is within REMINDER_WINDOW_DAYS days before (or on) the decode date."""
    if pd.isna(decode_date):
        return False
    days_left = (decode_date.date() - today.date()).days
    return 0 <= days_left <= REMINDER_WINDOW_DAYS

# -----------------------------------
# Data Loading and Management
# -----------------------------------

def generate_full_dataset():
    """Generate a complete dataset from scratch"""
    dates = build_decode_calendar(months_back=1, months_ahead=18)
    today = pd.Timestamp.today().normalize()
    
    activities = []
    for idx, row in dates.iterrows():
        month_name = row["DECODE MONTH"]
        decode_date = row["DATE"]
        
        activities.append({
            "ID": f"CHILD-{idx+1:04d}",
            "DECODE MONTH": month_name,
            "ASSIGNED PERSON": "",
            "ACTIVITY": f"CHILD Decode - {month_name}",
            "STATUS": "Pending" if decode_date >= today else "Overdue",
            "REMINDER SENT": "No",
            "DATE": decode_date
        })
    
    return pd.DataFrame(activities)

@st.cache_data
def load_data():
    """Load task data and merge with calendar-based decode dates"""
    
    if not os.path.exists(FILE):
        st.warning("CHILD_Decode_Tracker.xlsx not found. Generating data from calendar...")
        return generate_full_dataset()
    
    try:
        # Load the Excel file
        df = pd.read_excel(FILE, sheet_name="Decode Tasks")
        
        # Check if required columns exist
        if "DECODE MONTH" not in df.columns:
            st.warning("No 'DECODE MONTH' column found in Excel. Generating data from calendar...")
            return generate_full_dataset()
        
        # Build calendar dates
        calendar_dates = build_decode_calendar()
        
        # Clean up DECODE MONTH in Excel - strip whitespace and standardize
        df["DECODE MONTH"] = df["DECODE MONTH"].astype(str).str.strip()
        
        # Merge on DECODE MONTH
        df = df.merge(
            calendar_dates,
            on="DECODE MONTH",
            how="left"
        )
        
        # If merge failed, try to extract date from month name
        if "DATE" not in df.columns or df["DATE"].isna().all():
            st.info("Matching DECODE MONTH with calendar dates...")
            
            # Try to extract from the DECODE MONTH column itself
            dates_list = []
            for idx, row in df.iterrows():
                month_str = row["DECODE MONTH"]
                try:
                    # Try to parse the month string
                    if " " in month_str:
                        month, year = month_str.split()
                        # Convert month name to number
                        month_num = datetime.strptime(month, "%B").month
                        decode_date = last_saturday(int(year), month_num)
                        dates_list.append(decode_date)
                    else:
                        # Try other formats
                        decode_date = pd.to_datetime(month_str, errors='coerce')
                        dates_list.append(decode_date)
                except:
                    dates_list.append(pd.NaT)
            
            df["DATE"] = dates_list
        
        # Convert DATE to datetime
        df["DATE"] = pd.to_datetime(df["DATE"])
        
        # If still all NaT, generate dates from scratch
        if df["DATE"].isna().all():
            st.warning("Could not generate dates from Excel. Creating new dates from calendar.")
            df = generate_full_dataset()
        
        # Ensure REMINDER SENT column exists
        if "REMINDER SENT" not in df.columns:
            df["REMINDER SENT"] = "No"
        
        # Ensure STATUS column exists
        if "STATUS" not in df.columns:
            today = pd.Timestamp.today().normalize()
            df["STATUS"] = df["DATE"].apply(
                lambda d: "Pending" if d >= today else "Overdue"
            )
        
        # Ensure ID column exists
        if "ID" not in df.columns:
            df["ID"] = [f"CHILD-{i+1:04d}" for i in range(len(df))]
        
        # Ensure ASSIGNED PERSON column exists
        if "ASSIGNED PERSON" not in df.columns:
            df["ASSIGNED PERSON"] = ""
        
        # Ensure ACTIVITY column exists
        if "ACTIVITY" not in df.columns:
            df["ACTIVITY"] = df["DECODE MONTH"].apply(
                lambda x: f"CHILD Decode - {x}"
            )
        
        return df
        
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        st.info("Generating data from calendar instead...")
        return generate_full_dataset()

def save_data(df):
    """Persist task-level fields back to Excel, excluding the calendar-derived DATE column."""
    try:
        # Create a copy without the DATE column for saving
        df_to_save = df.drop(columns=["DATE"]).copy()
        df_to_save.to_excel(
            FILE,
            sheet_name="Decode Tasks",
            index=False
        )
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

# -----------------------------------
# Main App
# -----------------------------------

# Load data
df = load_data()
today = pd.Timestamp.today().normalize()

# If dataframe is empty, generate data
if df.empty:
    st.warning("No data available. Generating from calendar...")
    df = generate_full_dataset()

# -----------------------------------
# Daily Reminder Engine
# -----------------------------------

def run_reminder_engine(df, today):
    due_mask = (
        df["DATE"].apply(lambda d: in_reminder_window(d, today))
        & (df["STATUS"] == "Pending")
    )
    
    due_today = df[due_mask].copy()
    
    if not due_today.empty and (df.loc[due_mask, "REMINDER SENT"] != "Yes").any():
        df.loc[due_mask, "REMINDER SENT"] = "Yes"
        save_data(df)
    
    return df, due_today

df, due_today = run_reminder_engine(df, today)

# -----------------------------------
# Header
# -----------------------------------

st.markdown(
    """
    <div class="header">
    <h1>🧬 CHILD Decode Management Dashboard</h1>
    <p>Child Health and Mortality Prevention Surveillance (CHAMPS) Decode Activity Monitoring System</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# Reminder Banner
# -----------------------------------

if not due_today.empty:
    next_decode_in_window = due_today["DATE"].min()
    days_left = (next_decode_in_window.date() - today.date()).days
    
    activity_list = "".join(
        f"<li>{row['ACTIVITY']} — {row['ASSIGNED PERSON']}</li>"
        for _, row in due_today.iterrows()
    )
    
    st.markdown(
        f"""
        <div class="reminder-banner">
        <strong>⏰ Decode reminder:</strong>
        {days_left} day(s) left until the {next_decode_in_window.strftime('%d %B %Y')} decode
        (reminders run every day for the {REMINDER_WINDOW_DAYS} days before decode).
        <ul>
        {activity_list}
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------
# Summary Cards
# -----------------------------------

total_tasks = len(df)
pending = len(df[df["STATUS"] == "Pending"])
completed = len(df[df["STATUS"] == "Completed"])
overdue = len(df[(df["STATUS"] == "Pending") & (df["DATE"] < today)])

cols = st.columns(4)
summary = [
    ("Total Activities", total_tasks),
    ("Pending", pending),
    ("Completed", completed),
    ("Overdue", overdue)
]

for col, item in zip(cols, summary):
    col.markdown(
        f"""
        <div class="card">
        <div class="card-title">{item[0]}</div>
        <div class="card-value">{item[1]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# -----------------------------------
# Schedule
# -----------------------------------

st.subheader("📅 Decode Activity Schedule")

col1, col2 = st.columns(2)

with col1:
    month_options = sorted(df["DECODE MONTH"].unique())
    selected_month = st.multiselect("Filter by Decode Month", month_options)

with col2:
    person_options = sorted(df["ASSIGNED PERSON"].dropna().unique()) if "ASSIGNED PERSON" in df.columns else []
    selected_person = st.multiselect("Filter by Responsible Person", person_options)

filtered = df.copy()

if selected_month:
    filtered = filtered[filtered["DECODE MONTH"].isin(selected_month)]

if selected_person:
    filtered = filtered[filtered["ASSIGNED PERSON"].isin(selected_person)]

display = filtered.sort_values("DATE").copy()
display["DATE"] = display["DATE"].dt.strftime("%d %B %Y")

st.dataframe(
    display[["ID", "DATE", "ASSIGNED PERSON", "ACTIVITY", "STATUS", "REMINDER SENT"]],
    width="stretch",
    hide_index=True
)

st.divider()

# -----------------------------------
# Update Activity
# -----------------------------------

st.subheader("✏️ Update Activity Status")

task_id = st.selectbox("Select Activity", df["ID"].unique())
new_status = st.selectbox("New Status", ["Pending", "Completed", "Delayed"])
assigned_person = st.text_input(
    "Assigned Person",
    value=df[df["ID"] == task_id]["ASSIGNED PERSON"].iloc[0] if not df[df["ID"] == task_id]["ASSIGNED PERSON"].empty else ""
)

if st.button("💾 Save Update", type="primary"):
    df.loc[df["ID"] == task_id, "STATUS"] = new_status
    if assigned_person:
        df.loc[df["ID"] == task_id, "ASSIGNED PERSON"] = assigned_person
    save_data(df)
    st.success("✅ Activity updated successfully")
    st.rerun()

st.divider()

# -----------------------------------
# Next CHILD Decode
# -----------------------------------

st.subheader("🎯 Next CHILD Decode Cycle")

next_decode = get_next_decode(today)
days_left = (next_decode.date() - today.date()).days
reminder_note = (
    f"🔔 Inside the {REMINDER_WINDOW_DAYS}-day reminder window."
    if in_reminder_window(next_decode, today)
    else ""
)

st.info(
    f"""
    **Next CHILD Decode Date**
    📅 {next_decode.strftime('%d %B %Y')} (calculated as the last Saturday of the month)
    
    **Days Remaining**
    {days_left} days
    
    {reminder_note}
    """
)

st.divider()

# -----------------------------------
# Completed Activities
# -----------------------------------

st.subheader("✅ Recently Completed Activities")

completed_tasks = df[df["STATUS"] == "Completed"].sort_values("DATE", ascending=False)

if not completed_tasks.empty:
    completed_display = completed_tasks.copy()
    completed_display["DATE"] = completed_display["DATE"].dt.strftime("%d %B %Y")
    
    st.dataframe(
        completed_display[["DATE", "ASSIGNED PERSON", "ACTIVITY"]],
        width="stretch",
        hide_index=True
    )
else:
    st.write("No completed activities yet.")

st.divider()

# -----------------------------------
# Export / Reset
# -----------------------------------

col1, col2 = st.columns(2)

with col1:
    if st.button("📤 Export Data", type="secondary"):
        # Create a CSV download
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"CHILD_Decode_Data_{today.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("🔄 Regenerate from Calendar", type="secondary"):
        df = generate_full_dataset()
        save_data(df)
        st.success("✅ Data regenerated from calendar")
        st.rerun()

# Footer
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 20px; padding: 20px;">
    CHILD Decode Dashboard | Decode dates are always the last Saturday of each month
    </div>
    """,
    unsafe_allow_html=True
)
