import pickle
import smtplib
import json
import os

from urllib.parse import quote
from datetime import datetime

from email.mime.text import MIMEText

from app import app
from models import User

# ==========================
# Load Model
# ==========================

model = pickle.load(open("ml/spam_model.pkl", "rb"))

vectorizer = pickle.load(open("ml/vectorizer.pkl", "rb"))

# ==========================
# Function to Send Alert Email
# ==========================

def send_notification(sender_email,
                      sender_password,
                      target_email,
                      subject,
                      body):

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = target_email

    try:

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

        server.login(sender_email, sender_password)

        server.send_message(msg)

        server.quit()

        print(f"✅ Alert Email Sent to {target_email}!")

    except Exception as e:

        print("❌ Failed to send email:", e)

# ==========================
# Save Alert Notification
# ==========================

def save_alert(subject, body, user_email):

    gmail_link = f"https://mail.google.com/mail/u/0/#search/subject%3A%22{quote(subject)}%22"

    new_alert = {

        "subject": subject,

        "body": body,

        "full_body": body,

        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),

        "link": gmail_link,

        "type": "spam",

        "user_email": user_email
    }

    if os.path.exists("data/alerts.json"):

        with open("data/alerts.json", "r") as file:

            alerts = json.load(file)

    else:

        alerts = []

    alerts.append(new_alert)

    with open("data/alerts.json", "w") as file:

        json.dump(alerts, file, indent=4)

# ==========================
# Detect Spam Function
# ==========================

def detect_email(email_text):

    email_tfidf = vectorizer.transform([email_text])

    prediction = model.predict(email_tfidf)[0]

    with app.app_context():

        users = User.query.filter(
            User.app_email.isnot(None),
            User.app_password.isnot(None)
        ).all()

        if prediction == 1:

            print("🚫 SPAM DETECTED!")

            spam_subject = email_text[:40]

            spam_body = email_text[:300]

            for user in users:

                # Send Mail

                send_notification(

                    user.app_email,

                    user.app_password,

                    user.app_email,

                    spam_subject,

                    spam_body
                )

                # Save Notification

                save_alert(

                    spam_subject,

                    spam_body,

                    user.app_email
                )

        else:

            print("✅ Not Spam.")

# ==========================
# Test Example
# ==========================

if __name__ == "__main__":

    test_email = input(
        "Enter email content to check across all accounts:\n"
    )

    detect_email(test_email)