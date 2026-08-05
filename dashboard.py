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
# (this is now the ONLY source of truth for decode dates -
#  nothing is read from the Excel file for this)
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
    (last Saturday of each month). This replaces any DATE column that
    used to live in the Excel file.
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

        rows.append(
            {
                "DECODE MONTH": decode_date.strftime("%B %Y"),
                "DATE": decode_date
            }
        )

    return pd.DataFrame(rows)


def parse_decode_month(value):
    """
    Robustly turn whatever is in a DECODE MONTH cell into (year, month).
    Handles Timestamps, 'August 2026', 'Aug 2026', '2026-08', '08/2026',
    extra whitespace, different casing, etc. Returns None if it can't
    make sense of the value at all.
    """

    if pd.isna(value):
        return None

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.year, value.month

    text = str(value).strip()

    if not text:
        return None

    parsed = pd.to_datetime(text, errors="coerce")

    if pd.isna(parsed):
        # e.g. "August 2026" needs a day to parse cleanly
        parsed = pd.to_datetime("1 " + text, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.year, parsed.month


def decode_date_for_row(value):
    """Compute the calendar decode date (last Saturday) directly from a DECODE MONTH cell."""

    parsed = parse_decode_month(value)

    if parsed is None:
        return pd.NaT

    year, month = parsed

    return last_saturday(year, month)


def in_reminder_window(decode_date, today):
    """True if today is within REMINDER_WINDOW_DAYS days before (or on) the decode date."""

    if pd.isna(decode_date):
        return False

    days_left = (decode_date.date() - today.date()).days

    return 0 <= days_left <= REMINDER_WINDOW_DAYS


# -----------------------------------
# Load Data
# -----------------------------------

@st.cache_data
def load_data():

    if not os.path.exists(FILE):

        st.error(
            "CHILD_Decode_Tracker.xlsx not found. Run generate_tracker.py first."
        )

        st.stop()

    df = pd.read_excel(
        FILE,
        sheet_name="Decode Tasks"
    )

    # The Excel file no longer needs to (and should not) carry a DATE
    # column - if one is present we drop it, and always recompute the
    # decode date from the calendar instead. Each row's DECODE MONTH
    # cell is parsed directly (no string-matching against a separate
    # calendar table), so formatting differences in the Excel file
    # can't cause a silent mismatch.
    if "DATE" in df.columns:
        df = df.drop(columns=["DATE"])

    df["DATE"] = df["DECODE MONTH"].apply(decode_date_for_row)

    unparsed = df[df["DATE"].isna()]["DECODE MONTH"].unique()

    if len(unparsed) > 0:
        st.warning(
            "Could not read a decode date from these DECODE MONTH values - "
            "check their spelling/format in the Excel file: "
            + ", ".join(str(v) for v in unparsed)
        )

    if "REMINDER SENT" not in df.columns:
        df["REMINDER SENT"] = "No"

    return df


def save_data(df):
    """Persist task-level fields back to Excel, excluding the calendar-derived DATE column."""

    df.drop(columns=["DATE"]).to_excel(
        FILE,
        sheet_name="Decode Tasks",
        index=False
    )

    st.cache_data.clear()


df = load_data()

today = pd.Timestamp.today().normalize()


# -----------------------------------
# Daily Reminder Engine
# -----------------------------------
#
# NOTE: Streamlit only runs this code when someone opens/refreshes the
# app, so this can't fire on its own overnight. To truly "send" a
# reminder every day during the 7-day window, schedule something
# (cron, Task Scheduler, GitHub Actions, etc.) to hit this app - or a
# small companion script that imports build_decode_calendar() /
# in_reminder_window() - once a day. What's below covers everything
# that CAN live inside the app: it recomputes the window from the
# calendar (never from Excel) every time the app loads, flags the
# pending tasks that fall inside it, and marks them as reminded.

def run_reminder_engine(df):

    due_mask = (
        df["DATE"].apply(lambda d: in_reminder_window(d, today))
        & (df["STATUS"] == "Pending")
    )

    due_today = df[due_mask].copy()

    if not due_today.empty and (df.loc[due_mask, "REMINDER SENT"] != "Yes").any():
        df.loc[due_mask, "REMINDER SENT"] = "Yes"
        save_data(df)

    return df, due_today


df, due_today = run_reminder_engine(df)


# -----------------------------------
# Header
# -----------------------------------

st.markdown(
    """
    <div class="header">

    <h1>
    CHILD Decode Management Dashboard
    </h1>

    <p>
    Child Health and Mortality Prevention Surveillance (CHAMPS)
    Decode Activity Monitoring System
    </p>

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

pending = len(
    df[df["STATUS"] == "Pending"]
)

completed = len(
    df[df["STATUS"] == "Completed"]
)

overdue = len(
    df[
        (df["STATUS"] == "Pending")
        &
        (df["DATE"] < today)
    ]
)

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

        <div class="card-title">
        {item[0]}
        </div>

        <div class="card-value">
        {item[1]}
        </div>

        </div>
        """,

        unsafe_allow_html=True

    )


st.divider()


# -----------------------------------
# Schedule
# -----------------------------------

st.subheader(
    "Decode Activity Schedule"
)

col1, col2 = st.columns(2)

with col1:

    selected_month = st.multiselect(

        "Filter by Decode Month",

        sorted(
            df["DECODE MONTH"].unique()
        )

    )

with col2:

    selected_person = st.multiselect(

        "Filter by Responsible Person",

        sorted(
            df["ASSIGNED PERSON"].unique()
        )

    )

filtered = df.copy()

if selected_month:

    filtered = filtered[
        filtered["DECODE MONTH"].isin(
            selected_month
        )
    ]

if selected_person:

    filtered = filtered[
        filtered["ASSIGNED PERSON"].isin(
            selected_person
        )
    ]

display = filtered.sort_values(
    "DATE"
).copy()

display["DATE"] = display["DATE"].dt.strftime(
    "%d %B %Y"
)

st.dataframe(

    display[

        [

            "ID",

            "DATE",

            "ASSIGNED PERSON",

            "ACTIVITY",

            "STATUS",

            "REMINDER SENT"

        ]

    ],

    width="stretch",

    hide_index=True

)


st.divider()


# -----------------------------------
# Update Activity
# -----------------------------------

st.subheader(
    "Update Activity Status"
)

task_id = st.selectbox(

    "Select Activity",

    df["ID"]

)

new_status = st.selectbox(

    "New Status",

    [

        "Pending",

        "Completed",

        "Delayed"

    ]

)

if st.button(
    "Save Update",
    type="primary"
):

    df.loc[
        df["ID"] == task_id,
        "STATUS"
    ] = new_status

    save_data(df)

    st.success(
        "Activity updated successfully"
    )


st.divider()


# -----------------------------------
# Next CHILD Decode
# -----------------------------------

st.subheader(
    "Next CHILD Decode Cycle"
)

next_decode = get_next_decode(today)

days_left = (
    next_decode.date()
    -
    today.date()
).days

reminder_note = (
    f"🔔 Inside the {REMINDER_WINDOW_DAYS}-day reminder window."
    if in_reminder_window(next_decode, today)
    else ""
)

st.info(

    f"""

**Next CHILD Decode Date**

📅 {next_decode.strftime('%d %B %Y')}  (calculated as the last Saturday of the month)


**Days Remaining**

{days_left} days

{reminder_note}

"""

)


st.divider()


# -----------------------------------
# Completed Activities
# -----------------------------------

st.subheader(
    "Recently Completed Activities"
)

completed_tasks = df[
    df["STATUS"] == "Completed"
].sort_values(
    "DATE",
    ascending=False
)

if not completed_tasks.empty:

    completed_display = completed_tasks.copy()

    completed_display["DATE"] = (
        completed_display["DATE"]
        .dt.strftime("%d %B %Y")
    )

    st.dataframe(

        completed_display[

            [

                "DATE",

                "ASSIGNED PERSON",

                "ACTIVITY"

            ]

        ],

        width="stretch",

        hide_index=True

    )

else:

    st.write(
        "No completed activities yet."
    )
