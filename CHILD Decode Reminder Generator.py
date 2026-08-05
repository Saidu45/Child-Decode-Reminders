import pandas as pd
from datetime import datetime, timedelta
import calendar
import os


FILE = "CHILD_Decode_Tracker.xlsx"



# -----------------------------------
# Find last Saturday of a month
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


    return date




# -----------------------------------
# Generate activities for each decode
# -----------------------------------

def generate_schedule(year, month):

    decode_date = last_saturday(
        year,
        month
    )


    return [

        {
            "DATE": decode_date - timedelta(days=56),
            "ASSIGNED PERSON": "Rashid",
            "ACTIVITY": "Rashid sends list to Network Pathologists"
        },


        {
            "DATE": decode_date - timedelta(days=14),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Case packets sent to SMEs"
        },


        {
            "DATE": decode_date - timedelta(days=4),
            "ASSIGNED PERSON": "Rashid / Dr. Andrew / Aziz / Seyi",
            "ACTIVITY": "SMEs submit Decode Reports"
        },


        {
            "DATE": decode_date - timedelta(days=5),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Stakeholder memo sent for Dr. Ike's signature"
        },


        {
            "DATE": decode_date,
            "ASSIGNED PERSON": "Pathology Team",
            "ACTIVITY": "CHILD Decode"
        },


        {
            "DATE": decode_date + timedelta(days=2),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz/Bassey",
            "ACTIVITY": "Service Completion Certificate sent"
        },


        {
            "DATE": decode_date + timedelta(days=5),
            "ASSIGNED PERSON": "Rashid",
            "ACTIVITY": "Consensus Form sent"
        },


        {
            "DATE": decode_date + timedelta(days=7),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Upload Decode Report to REDCap"
        },


        {
            "DATE": decode_date + timedelta(days=7),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Send Decode Results to Surveillance"
        }

    ]




# -----------------------------------
# Generate tracker
# -----------------------------------

today = datetime.today()

year = today.year


all_tasks = []



# Generate current year and next year

for yr in [year, year + 1]:

    for month in range(1, 13):

        schedule = generate_schedule(
            yr,
            month
        )


        for task in schedule:


            # Keep only future activities

            if task["DATE"] >= today:


                all_tasks.append(

                    {

                        "DATE": task["DATE"],

                        "YEAR": yr,

                        "DECODE MONTH": calendar.month_name[month],

                        "ASSIGNED PERSON": task["ASSIGNED PERSON"],

                        "ACTIVITY": task["ACTIVITY"],

                        "STATUS": "Pending",

                        "REMINDER SENT": "No"

                    }

                )




# Create dataframe

df = pd.DataFrame(
    all_tasks
)



# Add ID

df.insert(
    0,
    "ID",
    range(
        1,
        len(df)+1
    )
)



# Sort dates

df = df.sort_values(
    "DATE"
).reset_index(
    drop=True
)



# Remove old file

if os.path.exists(FILE):

    os.remove(FILE)



# Export

df.to_excel(

    FILE,

    sheet_name="Decode Tasks",

    index=False

)



print(
    "CHILD Decode Tracker generated successfully"
)


print(
    f"Total future activities: {len(df)}"
)