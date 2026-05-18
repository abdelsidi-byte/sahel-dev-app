"""
Sahel Dev - Monitoring Worker
رصد APIs وإرسال التنبيهات
"""
import asyncio
import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, Monitor, Check, Incident, AlertChannel, User
from auth import hash_password
import smtplib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringWorker:
    """Worker يرصد APIs ويرسل التنبيهات"""

    def __init__(self):
        self.db = SessionLocal()

    def check_monitor(self, monitor: Monitor) -> dict:
        """فحص مونيتور واحد وإرجاع النتيجة"""
        start_time = datetime.utcnow()

        try:
            # HTTP request
            with httpx.Client(timeout=10) as client:
                response = client.request(
                    method=monitor.method,
                    url=monitor.url
                )

            end_time = datetime.utcnow()
            response_time = int((end_time - start_time).total_seconds() * 1000)

            is_up = response.status_code >= 200 and response.status_code < 400

            return {
                "success": True,
                "is_up": is_up,
                "status_code": response.status_code,
                "response_time": response_time,
                "error": None
            }

        except httpx.Timeout:
            return {
                "success": False,
                "is_up": False,
                "status_code": None,
                "response_time": None,
                "error": "Timeout"
            }
        except httpx.ConnectError:
            return {
                "success": False,
                "is_up": False,
                "status_code": None,
                "response_time": None,
                "error": "Connection Error"
            }
        except Exception as e:
            return {
                "success": False,
                "is_up": False,
                "status_code": None,
                "response_time": None,
                "error": str(e)
            }

    def record_check(self, monitor_id: int, result: dict):
        """تسجيل نتيجة الفحص في قاعدة البيانات"""
        check = Check(
            monitor_id=monitor_id,
            status_code=result.get("status_code"),
            response_time=result.get("response_time"),
            is_up=result.get("is_up", False),
            error_message=result.get("error")
        )
        self.db.add(check)
        self.db.commit()

    def handle_incident(self, monitor: Monitor, is_down: bool):
        """كشف Incident وإنشاء/حل"""
        if is_down:
            # فحص إذا كان يوجد Incident مفتوح
            open_incident = self.db.query(Incident).filter(
                Incident.monitor_id == monitor.id,
                Incident.status == "detected"
            ).first()

            if not open_incident:
                # إنشاء Incident جديد
                incident = Incident(
                    monitor_id=monitor.id,
                    status="detected"
                )
                self.db.add(incident)
                self.db.commit()
                logger.warning(f"🚨 Incident created for monitor {monitor.name}")

                # إرسال تنبيه
                self.send_alerts(monitor, "down")

        else:
            # الفحص ناجح - نحل أي Incident مفتوح
            open_incident = self.db.query(Incident).filter(
                Incident.monitor_id == monitor.id,
                Incident.status == "detected"
            ).first()

            if open_incident:
                open_incident.status = "resolved"
                open_incident.resolved_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"✅ Incident resolved for monitor {monitor.name}")

                # إرسال تنبيه
                self.send_alerts(monitor, "resolved")

    def send_alerts(self, monitor: Monitor, event: str):
        """إرسال تنبيهات لكل القنوات"""
        user = self.db.query(User).filter(User.id == monitor.user_id).first()
        if not user:
            return

        channels = self.db.query(AlertChannel).filter(
            AlertChannel.user_id == user.id,
            AlertChannel.is_active == True
        ).all()

        for channel in channels:
            try:
                if channel.channel_type == "email":
                    self._send_email(channel.config, monitor, event)
                elif channel.channel_type == "slack":
                    self._send_slack(channel.config, monitor, event)
                elif channel.channel_type == "discord":
                    self._send_discord(channel.config, monitor, event)
                elif channel.channel_type == "sms":
                    self._send_sms(channel.config, monitor, event)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.channel_type}: {e}")

    def _send_email(self, to_email: str, monitor: Monitor, event: str):
        """إرسال Email"""
        # في الإنتاج، استخدم SMTP الحقيقي
        # هنا مجرد logging للتطوير
        logger.info(f"📧 Email alert to {to_email}: {monitor.name} is {event}")

        # Example SMTP (uncomment in production):
        # with smtplib.SMTP("smtp.gmail.com", 587) as server:
        #     server.starttls()
        #     server.login("your-email@gmail.com", "your-password")
        #     message = f"Subject: {monitor.name} is {event}\n\nMonitor {monitor.name} is now {event}!"
        #     server.sendmail("alerts@saheldev.com", to_email, message)

    def _send_slack(self, webhook_url: str, monitor: Monitor, event: str):
        """إرسال Slack Webhook"""
        emoji = "🔴" if event == "down" else "🟢"
        status_text = "متوقف" if event == "down" else "شغال"

        payload = {
            "text": f"{emoji} *{monitor.name}* - الحالة: *{status_text}*\nURL: {monitor.url}"
        }

        try:
            with httpx.Client() as client:
                client.post(webhook_url, json=payload, timeout=10)
            logger.info(f"📤 Slack alert sent for {monitor.name}")
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")

    def _send_discord(self, webhook_url: str, monitor: Monitor, event: str):
        """إرسال Discord Webhook"""
        emoji = "🔴" if event == "down" else "🟢"
        status_text = "متوقف" if event == "down" else "شغال"
        color = 15158332 if event == "down" else 3066993  # Red or Green

        payload = {
            "embeds": [{
                "title": f"{emoji} {monitor.name}",
                "description": f"الحالة: **{status_text}**\nURL: {monitor.url}",
                "color": color
            }]
        }

        try:
            with httpx.Client() as client:
                client.post(webhook_url, json=payload, timeout=10)
            logger.info(f"📤 Discord alert sent for {monitor.name}")
        except Exception as e:
            logger.error(f"Discord alert failed: {e}")

    def _send_sms(self, phone: str, monitor: Monitor, event: str):
        """إرسال SMS ( عبر Twilio مثلاً )"""
        # في الإنتاج، استخدم Twilio أو similar
        logger.info(f"📱 SMS alert to {phone}: {monitor.name} is {event}")

        # Example Twilio (uncomment in production):
        # from twilio.rest import Client
        # client = Client("account_sid", "auth_token")
        # client.messages.create(
        #     body=f"Sahel Dev Alert: {monitor.name} is {event}",
        #     from_="+1234567890",
        #     to=phone
        # )

    def run_check(self, monitor_id: int):
        """تشغيل فحص واحد"""
        monitor = self.db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if not monitor or not monitor.is_active:
            return

        logger.info(f"Checking: {monitor.name} ({monitor.url})")

        result = self.check_monitor(monitor)
        self.record_check(monitor_id, result)
        self.handle_incident(monitor, not result["is_up"])

    def run_all(self):
        """فحص كل المونيتورات النشطة"""
        monitors = self.db.query(Monitor).filter(Monitor.is_active == True).all()
        logger.info(f"Running check for {len(monitors)} monitors")

        for monitor in monitors:
            self.run_check(monitor.id)

    def get_uptime_stats(self, monitor_id: int, days: int = 30) -> dict:
        """حساب إحصائيات Uptime"""
        from datetime import timedelta
        from sqlalchemy import func

        since = datetime.utcnow() - timedelta(days=days)
        checks = self.db.query(Check).filter(
            Check.monitor_id == monitor_id,
            Check.checked_at >= since
        ).all()

        if not checks:
            return {"uptime": 0, "total": 0, "avg_response": 0}

        total = len(checks)
        up = sum(1 for c in checks if c.is_up)
        response_times = [c.response_time for c in checks if c.response_time]

        return {
            "uptime": round((up / total) * 100, 2) if total > 0 else 0,
            "total": total,
            "avg_response": round(sum(response_times) / len(response_times), 0) if response_times else 0
        }


# تشغيل Worker
if __name__ == "__main__":
    logger.info("🚀 Starting Sahel Dev Monitoring Worker")

    worker = MonitoringWorker()

    # تشغيل فحص واحد
    worker.run_all()

    logger.info("✅ Monitoring check completed")


# دالة للاستخدام كـ cronjob
def run_monitoring():
    worker = MonitoringWorker()
    worker.run_all()