import smtplib
from email.mime.text import MIMEText

def send_email_alert(bin_id, location, level):
    sender_email = "YOUR_EMAIL@gmail.com"
    sender_password = "YOUR_APP_PASSWORD"
    receiver_email = "municipality@gmail.com"

    subject = "Dustbin Full Alert"
    body = f"Dustbin {bin_id} at {location} is FULL.\nCurrent Level: {level}%"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email Alert Sent")
    except Exception as e:
        print("Email Error:", e)