# CHILD Decode Reminder System

## Overview

The **CHILD Decode Reminder System** is a Python and Streamlit-based application designed to manage, track, and automate reminders for activities associated with the **CHAMPS CHILD Decode process**.

CHILD Decode is conducted on the **last Saturday of every month**.

The system automatically calculates the monthly Decode date, generates the activities that must be completed before and after each Decode, tracks their status, and supports automated email reminders to responsible team members.

---

## CHILD Decode Schedule

For every CHILD Decode cycle, the system schedules the following activities:

| Timeline               | Assigned Person                   | Activity                                      |
| ---------------------- | --------------------------------- | --------------------------------------------- |
| 8 weeks before Decode  | Rashid                            | Send list/request to Network Pathologists     |
| 2 weeks before Decode  | Drs. Andrew/Aziz                  | Send case packets to SMEs                     |
| Tuesday before Decode  | Rashid / Dr. Andrew / Aziz / Seyi | SMEs submit Decode Reports                    |
| During Decode Week     | Drs. Andrew/Aziz                  | Send stakeholder memo for Dr. Ike's signature |
| Last Saturday of Month | Pathology Team                    | CHILD Decode                                  |
| Monday after Decode    | Drs. Andrew/Aziz/Bassey           | Send Service Completion Certificate           |
| Thursday after Decode  | Rashid                            | Send Consensus Form                           |
| 1 week after Decode    | Drs. Andrew/Aziz                  | Upload Decode Report to REDCap                |
| 1 week after Decode    | Drs. Andrew/Aziz                  | Send Decode Results to Surveillance           |

### Example

For **August 2026**, the last Saturday is:

**29 August 2026**

Therefore, the CHILD Decode for August 2026 is scheduled for **Saturday, 29 August 2026**, with all related activities calculated around this date.

---

## Features

The CHILD Decode Reminder System provides the following functionality:

* Automatically identifies the **last Saturday of every month**.
* Generates CHILD Decode activities for upcoming Decode cycles.
* Automatically calculates activities before and after each Decode.
* Tracks activities as **Pending, Completed, or Delayed**.
* Identifies overdue activities.
* Tracks whether email reminders have already been sent.
* Provides a Streamlit dashboard for monitoring Decode activities.
* Allows filtering of activities by Decode month and responsible person.
* Allows activity status to be updated from the dashboard.
* Displays the next CHILD Decode date.
* Displays the number of days remaining until the next Decode.
* Supports automated email reminders for activities due on the current day.
* Maintains a central Excel tracker for CHILD Decode activities.

---

## Project Structure

```text
Child-Decode-Reminders/
│
├── child_dashboard.py
├── child_reminder.py
├── outlook_email_child.py
├── CHILD Decode Reminder Generator.py
├── CHILD_Decode_Tracker.xlsx
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Main Components

### `CHILD Decode Reminder Generator.py`

This script automatically determines the **last Saturday of each month** and generates all activities associated with each CHILD Decode cycle.

The generated activities are stored in:

```text
CHILD_Decode_Tracker.xlsx
```

Run the generator whenever the CHILD Decode tracker needs to be created or updated.

---

### `CHILD_Decode_Tracker.xlsx`

This is the main tracker used by the system.

It contains information such as:

* Activity ID
* Scheduled Date
* Year
* Decode Month
* Assigned Person
* Activity
* Status
* Reminder Sent

The tracker is used by both the Streamlit dashboard and the automated reminder system.

---

### `child_dashboard.py`

This is the Streamlit application used to monitor CHILD Decode activities.

The dashboard provides:

* Total number of activities
* Pending activities
* Completed activities
* Overdue activities
* CHILD Decode activity schedule
* Filters by Decode month
* Filters by responsible person
* Activity status updates
* Next CHILD Decode date
* Days remaining until the next Decode
* Recently completed activities

---

### `child_reminder.py`

This script checks the CHILD Decode tracker for activities scheduled for the current date.

A reminder is sent when an activity meets the following conditions:

```text
DATE = Today
STATUS = Pending
REMINDER SENT = No
```

After a reminder is successfully sent, the tracker is updated:

```text
REMINDER SENT = Yes
```

This prevents the same reminder from being sent repeatedly.

---

### `outlook_email_child.py`

This module handles the email functionality used by the CHILD Decode Reminder System.

It allows the reminder script to send automated notifications to the responsible team members.

Email credentials should **not be stored directly in the source code or uploaded to GitHub**.

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd Child-Decode-Reminders
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## Requirements

The `requirements.txt` file should contain at least:

```text
streamlit
pandas
openpyxl
python-dotenv
```

Additional dependencies can be added if required.

---

## Generate the CHILD Decode Tracker

Run:

```bash
python "CHILD Decode Reminder Generator.py"
```

The script will generate:

```text
CHILD_Decode_Tracker.xlsx
```

The tracker contains upcoming CHILD Decode activities and their scheduled dates.

---

## Run the Dashboard Locally

Start the Streamlit application using:

```bash
streamlit run child_dashboard.py
```

The CHILD Decode Management Dashboard should automatically open in your web browser.

---

## Run the Reminder System

To manually check for reminders due today, run:

```bash
python child_reminder.py
```

The script will:

1. Open the CHILD Decode tracker.
2. Check today's date.
3. Find pending activities due today.
4. Identify the responsible person.
5. Send the email reminder.
6. Mark the reminder as sent.
7. Save the updated tracker.

The reminder script can also be configured to run automatically using a scheduled task.

---

## Streamlit Deployment

The CHILD Decode dashboard can be deployed using **Streamlit Community Cloud**.

When creating the Streamlit application, configure:

```text
Branch: main
Main file path: child_dashboard.py
```

Make sure the following files are committed to the GitHub repository:

```text
child_dashboard.py
CHILD_Decode_Tracker.xlsx
requirements.txt
```

---

## Email Configuration

Sensitive information such as email usernames, passwords, application passwords, or authentication credentials should **never be committed to GitHub**.

For local development, credentials can be stored using environment variables in a `.env` file.

Make sure `.env` is included in `.gitignore`.

Example:

```text
.env
__pycache__/
*.pyc
```

This prevents sensitive credentials and unnecessary Python cache files from being uploaded to the repository.

---

## Workflow

The general CHILD Decode workflow is:

```text
Network Pathology Preparation
        ↓
Case Packets Prepared and Sent
        ↓
SMEs Review Cases
        ↓
SMEs Submit Decode Reports
        ↓
Stakeholder Memo
        ↓
CHILD Decode
        ↓
Service Completion
        ↓
Consensus Form
        ↓
Upload Decode Report to REDCap
        ↓
Send Decode Results to Surveillance
```

---

## Purpose

The CHILD Decode Reminder System was developed to improve the coordination and timely completion of activities surrounding the **CHAMPS CHILD Decode process**.

The system provides a structured way to monitor Decode activities, responsible personnel, deadlines, completion status, and reminders.

By automating schedule generation and reminders, the system helps reduce missed activities and provides the team with a centralized view of the CHILD Decode workflow.

---

## Technologies Used

* **Python**
* **Streamlit**
* **Pandas**
* **OpenPyXL**
* **Excel**
* **Email/SMTP Automation**
* **GitHub**
* **Streamlit Community Cloud**

---

## Project

**CHAMPS CHILD Decode Management and Reminder System**
