import smtplib
import json
import os

from urllib.parse import quote
from email.mime.text import MIMEText
from datetime import datetime

EMAIL = "janisannigandla226@gmail.com"
PASSWORD = "hnhtecmpkgykfyva"


def send_notification(to_email, subject, body):

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    # Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(EMAIL, PASSWORD)

    server.send_message(msg)

    server.quit()

    print("✅ Email sent successfully!")

    # =========================
    # SAVE ALERT NOTIFICATION
    # =========================

    gmail_link = f"https://mail.google.com/mail/u/0/#search/{quote(subject)}"

    new_alert = {
        "subject": subject,
        "body": body,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "link": gmail_link,
        "user_email": to_email
    }

    # Load existing alerts

    if os.path.exists("data/alerts.json"):

        with open("data/alerts.json", "r") as file:
            alerts = json.load(file)

    else:
        alerts = []

    # Add new alert

    alerts.append(new_alert)

    # Save alerts

    with open("data/alerts.json", "w") as file:
        json.dump(alerts, file, indent=4)


# Test

send_notification(
    "janisannigandla226@gmail.com",
    "Spam Alert",
    "A spam email was detected."
)