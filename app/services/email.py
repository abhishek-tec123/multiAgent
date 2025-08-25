# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# from app.core.config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL
# from app.core.logging_utils import get_logger


# logger = get_logger()


# class EmailService:
#     def send_email(self, subject: str, body: str) -> str:
#         message = MIMEMultipart()
#         message["From"] = SENDER_EMAIL
#         message["To"] = RECEIVER_EMAIL
#         message["Subject"] = subject
#         message.attach(MIMEText(body, "plain"))

#         try:
#             with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#                 server.starttls()
#                 server.login(SENDER_EMAIL, SENDER_PASSWORD)
#                 server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
#             logger.info("Email sent successfully.")
#             return "success"
#         except Exception as e:
#             logger.error(f"Email failed: {e}")
#             return f"failed: {e}"


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
from app.core.logging_utils import get_logger

logger = get_logger()


class EmailService:
    def send_email(self, subject: str, body: str, to_email: str) -> str:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, to_email, message.as_string())
            logger.info(f"Email sent successfully to {to_email}.")
            return "success"
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return f"failed: {e}"
