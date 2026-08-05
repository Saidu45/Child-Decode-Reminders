import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta


FILE = "CHILD_Decode_Tracker.xlsx"


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

    </style>
    """,
    unsafe_allow_html=True
)



# -----------------------------------
# Calculate CHILD Decode Date
# -----------------------------------

def last_saturday(year, month):

    last_day = calendar.monthrange(
        year,
        month
    )[1]

    date = datetime(
        year,
        month,
        last_day
    )

    while date.weekday() != 5:
        date -= timedelta(days=1)

    return pd.Timestamp(date)



def get_next_decode():

    today = pd.Timestamp.today().normalize()

    current_year = today.year
    current_month = today.month


    for month_offset in range(0,12):

        month = current_month + month_offset
        year = current_year

        if month > 12:
            month -= 12
            year += 1


        decode_date = last_saturday(
            year,
            month
        )


        if decode_date >= today:

            return decode_date



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


    df["DATE"] = pd.to_datetime(
        df["DATE"]
    )


    return df



df = load_data()



today = pd.Timestamp.today().normalize()



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
# Summary Cards
# -----------------------------------

total_tasks = len(df)


pending = len(
    df[df["STATUS"]=="Pending"]
)


completed = len(
    df[df["STATUS"]=="Completed"]
)


overdue = len(
    df[
        (df["STATUS"]=="Pending")
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


    df.to_excel(

        FILE,

        sheet_name="Decode Tasks",

        index=False

    )


    st.cache_data.clear()


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



next_decode = get_next_decode()



days_left = (
    next_decode.date()
    -
    today.date()
).days



st.info(

    f"""

**Next CHILD Decode Date**

📅 {next_decode.strftime('%d %B %Y')}


**Days Remaining**

{days_left} days

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
    df["STATUS"]=="Completed"
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
