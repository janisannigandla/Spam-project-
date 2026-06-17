import imaplib
import email
from email.header import decode_header
import pickle
import json
import os
import re
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from app import app
from models import User

model = pickle.load(open("ml/spam_model.pkl", "rb"))
vectorizer = pickle.load(open("ml/vectorizer.pkl", "rb"))

priority_patterns = [
    r'\b(?:urgent|asap|immediately|deadline|action required|attention needed)\b',
    r'\b(?:payment overdue|invoice attached|account suspended|verify your identity)\b',
    r'\b(?:job offer|final interview|offer letter|onboarding)\b',
    r'\b(?:flight details|booking confirmation|itinerary)\b'
]


def save_alert(file, data):

    print("\n===================")
    print("SAVING TO:", os.path.abspath(file))
    print("===================\n")

    if os.path.exists(file):
        with open(file, "r") as f:
            alerts = json.load(f)
    else:
        alerts = []

    # Prevent duplicates
    for alert in alerts:
        if (
            alert.get("email_id") == data.get("email_id")
            and alert.get("user_email") == data.get("user_email")
        ):
            print("EMAIL ALREADY EXISTS")
            return

    alerts.append(data)

    with open(file, "w") as f:
        json.dump(alerts, f, indent=2)

    print("ALERT SAVED SUCCESSFULLY")


def monitor_all_users():

    with app.app_context():

        users = User.query.filter(
            User.app_email.isnot(None),
            User.app_password.isnot(None)
        ).all()

        print("TOTAL USERS:", len(users))

        for user in users:

            EMAIL = user.app_email
            PASSWORD = user.app_password

            print("\nUSER:", EMAIL)

            mail = None

            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(EMAIL, PASSWORD)
                mail.select("inbox")

                status, messages = mail.search(None, "ALL")

                if not messages[0]:
                    print("No unread emails.")
                    continue

                for num in messages[0].split()[-10:]:

                    print("Fetching email:", num.decode())

                    status, msg_data = mail.fetch(num, "(RFC822)")

                    for part in msg_data:

                        if not isinstance(part, tuple):
                            continue

                        msg = email.message_from_bytes(part[1])

                        subject, encoding = decode_header(
                            msg["Subject"]
                        )[0]

                        if isinstance(subject, bytes):
                            subject = subject.decode(
                                encoding or "utf-8",
                                errors="ignore"
                            )

                        body = ""

                        if msg.is_multipart():

                            for p in msg.walk():

                                content_type = p.get_content_type()
                                content_disposition = str(
                                    p.get("Content-Disposition", "")
                                )

                                if (
                                    content_type == "text/plain"
                                    and "attachment"
                                    not in content_disposition
                                ):

                                    body_bytes = p.get_payload(
                                        decode=True
                                    )

                                    if body_bytes:
                                        body = body_bytes.decode(
                                            "utf-8",
                                            errors="ignore"
                                        )
                                        break

                        else:

                            body_bytes = msg.get_payload(
                                decode=True
                            )

                            if body_bytes:
                                body = body_bytes.decode(
                                    "utf-8",
                                    errors="ignore"
                                )

                        text = body.lower()

                        vector = vectorizer.transform([body])

                        pred = model.predict(vector)[0]

                        print("Subject:", subject)
                        print("Prediction:", pred)

                        alert_data = {
                            "user_email": EMAIL,
                            "email_id": num.decode(),
                            "subject": subject,
                            "body": body[:150],
                            "full_body": body,
                            "gmail_link": "https://mail.google.com/mail/u/0/#inbox"
                        }

                        # SPAM MAIL
                        if pred == 1:

                            alert_data["type"] = "spam"

                            save_alert(
                                "data/alerts.json",
                                alert_data
                            )

                        # NORMAL MAIL
                        else:

                            alert_data["type"] = "ham"

                            is_priority = False

                            for pattern in priority_patterns:

                                if re.search(pattern, text):
                                    is_priority = True
                                    break

                            if is_priority:

                                priority_data = alert_data.copy()

                                priority_data["link"] = (
                                    "https://mail.google.com/"
                                )

                                save_alert(
                                    "data/priority.json",
                                    priority_data
                                )

            except Exception as e:

                print(
                    f"Skipping {EMAIL} due to error: {e}"
                )

            finally:

                if mail is not None:

                    try:
                        mail.logout()
                    except:
                        pass


import time

if __name__ == "__main__":
    while True:
        print("Checking emails...")
        monitor_all_users()
        time.sleep(30)   # check every 30 seconds