import logging
import smtplib
from email.message import EmailMessage

from config.settings import Settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.email_host = Settings.SMTP_HOST
        self.email_port = Settings.SMTP_PORT
        self.email_user = Settings.SMTP_USER
        self.email_password = Settings.SMTP_PASSWORD
        self.enabled = Settings.SMTP_ENABLED

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('SMTP disabled; skip email to %s (%s)', to, subject)
            return False

        if not self.email_host or not self.email_user or not self.email_password:
            logger.warning('SMTP not configured; skip email to %s', to)
            return False

        try:
            message = EmailMessage()
            message['Subject'] = subject
            message['From'] = self.email_user
            message['To'] = to
            message.set_content(body)

            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)

            logger.info('Email sent to %s', to)
            return True
        except Exception:
            logger.exception('Failed to send email to %s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\n'
            f'Status: {task.status}'
        )
        self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f'Task atrasada: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' está atrasada!\n\n"
            f'Data limite: {task.due_date}'
        )
        self.send_email(user.email, subject, body)


notification_service = NotificationService()
