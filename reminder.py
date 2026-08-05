import pandas as pd
from datetime import datetime
from outlook_email import send_email


FILE = "CHILD_Decode_Tracker.xlsx"


# -----------------------------------
# Email Directory
# -----------------------------------

EMAILS = {

    "Rashid":
        "rashid@emory.edu",

    "Drs. Andrew/Aziz":
        "amosera@emory.edu;saaziz2@emory.edu",
    
    "Drs. Aziz":
            "saaziz2@emory.edu",
            
    "Seyi":
        "obalog2@emory.edu",

    "Pathology Team":
        "adaram2@emory.edu",

    "Drs. Bassey":
        "ibassey@emory.edu"

}


# -----------------------------------
# Load Decode Tracker
# -----------------------------------

df = pd.read_excel(
    FILE,
    sheet_name="Decode Tasks"
)


df["DATE"] = pd.to_datetime(
    df["DATE"]
).dt.normalize()


today = pd.Timestamp.today().normalize()


emails_sent = 0


# -----------------------------------
# Check Activities Due Today
# -----------------------------------

for index, row in df.iterrows():

    if (
        row["DATE"] == today
        and row["STATUS"] == "Pending"
        and row["REMINDER SENT"] == "No"
    ):


        recipient = EMAILS.get(
            row["ASSIGNED PERSON"]
        )


        if not recipient:

            print(
                f"No email configured for {row['ASSIGNED PERSON']}"
            )

            continue



        subject = (
            f"CHILD Decode Reminder: "
            f"{row['ACTIVITY']}"
        )


        body = f"""

Dear Team Member,


This is a reminder from the CHAMPS CHILD Decode Management System.


Activity:
{row['ACTIVITY']}


Assigned Person:
{row['ASSIGNED PERSON']}


Scheduled Date:
{row['DATE'].strftime('%d %B %Y')}


Current Status:
{row['STATUS']}


Please ensure this activity is completed according to the CHILD Decode schedule.


Regards,

CHAMPS Data Management Team

"""



        try:

            send_email(
                recipient,
                subject,
                body
            )


            df.loc[
                index,
                "REMINDER SENT"
            ] = "Yes"



            emails_sent += 1


            print(
                f"Reminder sent to {recipient}"
            )



        except Exception as e:


            print(
                f"Failed to send reminder to {recipient}"
            )


            print(e)



# -----------------------------------
# Save Tracker Updates
# -----------------------------------

df.to_excel(
    FILE,
    sheet_name="Decode Tasks",
    index=False
)


print("--------------------------------")
print("Reminder check completed.")
print(f"Emails sent: {emails_sent}")
print("--------------------------------")