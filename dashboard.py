import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title="CHILD Decode Management",
    page_icon="🧬",
    layout="wide"
)

# Styling
st.markdown(
    """
    <style>
    .main { background-color:#f8fafc; }
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
    .card-title { font-size:14px; color:#64748b; }
    .card-value { font-size:30px; font-weight:bold; color:#0f172a; }
    .status-pending { color:#f59e0b; font-weight:bold; }
    .status-completed { color:#10b981; font-weight:bold; }
    .status-overdue { color:#ef4444; font-weight:bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# Core Date Functions
# -----------------------------------

def last_saturday(year, month):
    """Calculate the last Saturday of a given month"""
    last_day = calendar.monthrange(year, month)[1]
    date = datetime(year, month, last_day)
    # Saturday is weekday 5 (Monday=0, Sunday=6)
    while date.weekday() != 5:
        date -= timedelta(days=1)
    return date

def get_decode_dates(start_date=None, num_months=12):
    """Get CHILD Decode dates for the next N months"""
    if start_date is None:
        start_date = datetime.now()
    
    dates = []
    year = start_date.year
    month = start_date.month
    
    for i in range(num_months):
        decode_date = last_saturday(year, month)
        dates.append(decode_date)
        
        # Move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return dates

def get_activity_status(decode_date, today):
    """Determine the status of an activity based on today's date"""
    if decode_date.date() < today.date():
        return "Overdue"
    elif decode_date.date() == today.date():
        return "Today"
    else:
        return "Pending"

def generate_activities(num_months=12):
    """Generate all activities based on decode dates"""
    today = datetime.now().date()
    decode_dates = get_decode_dates(num_months=num_months)
    
    activities = []
    for i, date in enumerate(decode_dates, 1):
        # Calculate status
        if date.date() < today:
            status = "Overdue"
        elif date.date() == today:
            status = "Today"
        else:
            status = "Pending"
        
        # Generate month name
        month_name = date.strftime("%B %Y")
        decode_month = date.strftime("%Y-%m")
        
        # Create activity entries
        activities.append({
            "ID": f"CHILD-{i:04d}",
            "DATE": date,
            "DECODE MONTH": decode_month,
            "MONTH NAME": month_name,
            "ASSIGNED PERSON": "",  # Will be assigned later
            "ACTIVITY": f"CHILD Decode - {month_name}",
            "STATUS": status,
            "REMINDER SENT": "No",
            "DAYS UNTIL": (date.date() - today).days if status == "Pending" else 0
        })
    
    return pd.DataFrame(activities)

# -----------------------------------
# Load/Save Data (Optional - for persistence)
# -----------------------------------

def load_data():
    """Load data from session state or generate new"""
    if 'df' not in st.session_state:
        # Check if there's a saved state
        st.session_state.df = generate_activities(12)
    return st.session_state.df

def save_data(df):
    """Save data to session state"""
    st.session_state.df = df

# -----------------------------------
# Main App
# -----------------------------------

# Load data
df = load_data()
today = pd.Timestamp.today().normalize()

# Header
st.markdown(
    """
    <div class="header">
    <h1>🧬 CHILD Decode Management Dashboard</h1>
    <p>Child Health and Mortality Prevention Surveillance (CHAMPS) Decode Activity Monitoring System</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Summary Cards
total_tasks = len(df)
pending = len(df[df["STATUS"] == "Pending"])
overdue = len(df[df["STATUS"] == "Overdue"])
completed = len(df[df["STATUS"] == "Completed"])

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
# Schedule View with Filters
# -----------------------------------

st.subheader("📅 Decode Activity Schedule")

col1, col2 = st.columns(2)

with col1:
    month_options = sorted(df["DECODE MONTH"].unique())
    selected_month = st.multiselect("Filter by Decode Month", month_options)

with col2:
    person_options = sorted(df["ASSIGNED PERSON"].unique())
    selected_person = st.multiselect("Filter by Responsible Person", person_options)

# Apply filters
filtered = df.copy()
if selected_month:
    filtered = filtered[filtered["DECODE MONTH"].isin(selected_month)]
if selected_person:
    filtered = filtered[filtered["ASSIGNED PERSON"].isin(selected_person)]

# Display filtered data
display = filtered.sort_values("DATE").copy()
display["DATE"] = display["DATE"].dt.strftime("%d %B %Y")

# Color-code status
def color_status(val):
    if val == "Pending":
        return "color: #f59e0b; font-weight: bold;"
    elif val == "Completed":
        return "color: #10b981; font-weight: bold;"
    elif val == "Overdue":
        return "color: #ef4444; font-weight: bold;"
    elif val == "Today":
        return "color: #3b82f6; font-weight: bold;"
    return ""

st.dataframe(
    display[["ID", "DATE", "ASSIGNED PERSON", "ACTIVITY", "STATUS", "REMINDER SENT"]],
    column_config={
        "STATUS": st.column_config.TextColumn("Status"),
    },
    width="stretch",
    hide_index=True
)

st.divider()

# -----------------------------------
# Update Activity Status
# -----------------------------------

st.subheader("✏️ Update Activity Status")

col1, col2, col3 = st.columns(3)

with col1:
    task_id = st.selectbox("Select Activity", df["ID"].unique())

with col2:
    new_status = st.selectbox("New Status", ["Pending", "Completed", "Overdue", "Today"])

with col3:
    assigned_person = st.text_input("Assigned Person", value=df[df["ID"] == task_id]["ASSIGNED PERSON"].iloc[0] if task_id in df["ID"].values else "")

if st.button("💾 Save Update", type="primary"):
    # Update status
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

next_decode = get_decode_dates(num_months=1)[0] if get_decode_dates(num_months=1) else None

if next_decode:
    days_left = (next_decode.date() - today.date()).days
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Next Decode Date",
            next_decode.strftime('%d %B %Y'),
            delta=None
        )
    with col2:
        st.metric(
            "Days Remaining",
            days_left,
            delta=None
        )
    with col3:
        if days_left < 0:
            st.warning("⚠️ This decode cycle has passed")
        elif days_left <= 7:
            st.warning("⚠️ Coming up soon!")
        else:
            st.success("✅ On track")

st.divider()

# -----------------------------------
# Recently Completed
# -----------------------------------

st.subheader("✅ Recently Completed Activities")

completed_tasks = df[df["STATUS"] == "Completed"].sort_values("DATE", ascending=False)

if not completed_tasks.empty:
    completed_display = completed_tasks.copy()
    completed_display["DATE"] = completed_display["DATE"].dt.strftime("%d %B %Y")
    
    st.dataframe(
        completed_display[["DATE", "MONTH NAME", "ASSIGNED PERSON", "ACTIVITY"]],
        width="stretch",
        hide_index=True
    )
else:
    st.info("No completed activities yet.")

st.divider()

# -----------------------------------
# Activity Calendar View
# -----------------------------------

st.subheader("📊 Activity Calendar")

# Create a simple calendar view
if not df.empty:
    # Group by month
    monthly_counts = df.groupby(["DECODE MONTH", "STATUS"]).size().unstack(fill_value=0)
    
    if not monthly_counts.empty:
        # Display as a bar chart
        st.bar_chart(monthly_counts)
        
        # Also show as table
        st.dataframe(monthly_counts)

st.divider()

# -----------------------------------
# Reset/Regenerate Data
# -----------------------------------

if st.button("🔄 Regenerate Activities", type="secondary"):
    st.session_state.df = generate_activities(12)
    st.success("✅ Activities regenerated successfully")
    st.rerun()

# Footer
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 20px; padding: 20px;">
    CHILD Decode Dashboard | Generated automatically based on CHAMPS decode schedule
    </div>
    """,
    unsafe_allow_html=True
)
