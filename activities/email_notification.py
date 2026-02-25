"""
Email notification activity for sending incident alerts via SMTP.

Uses internal SMTP relay (no authentication required).
SMTP details provided by infrastructure team.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

from temporalio import activity

from .logger import email_logger as logger
from props import SMTP_HOST, SMTP_IP, SMTP_PORT, EMAIL_SENDER, EMAIL_RECIPIENTS, TZ


@dataclass
class EmailInput:
    ip: str
    protocol: str
    poll_id: str
    incidents: List[Dict[str, Any]]
    total_interfaces: int


@dataclass
class EmailOutput:
    emails_sent: int = 0
    emails_failed: int = 0
    recipients: List[str] = field(default_factory=list)


def build_incident_email(ip: str, poll_id: str, incidents: List[Dict[str, Any]], total_interfaces: int) -> str:
    """Build HTML email body for incident notification."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count severities
    severity_counts = {}
    for inc in incidents:
        sev = inc.get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    severity_colors = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "warning": "#17a2b8",
    }

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h2 {{ color: #333; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th {{ background: #343a40; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #dee2e6; }}
            tr:nth-child(even) {{ background: #f8f9fa; }}
            .severity-critical {{ color: #dc3545; font-weight: bold; }}
            .severity-high {{ color: #fd7e14; font-weight: bold; }}
            .severity-medium {{ color: #ffc107; font-weight: bold; }}
            .severity-warning {{ color: #17a2b8; font-weight: bold; }}
            .footer {{ margin-top: 20px; color: #6c757d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h2>CRC Error Incident Alert</h2>
        <div class="summary">
            <p><strong>ACI Host:</strong> {ip}</p>
            <p><strong>Poll ID:</strong> {poll_id}</p>
            <p><strong>Timestamp:</strong> {timestamp} ({TZ})</p>
            <p><strong>Total Interfaces Monitored:</strong> {total_interfaces}</p>
            <p><strong>Total Incidents:</strong> {len(incidents)}</p>
"""

    # Add severity breakdown
    for sev, count in sorted(severity_counts.items()):
        color = severity_colors.get(sev, "#333")
        html += f'            <p><strong style="color: {color};">{sev.upper()}:</strong> {count}</p>\n'

    html += """
        </div>

        <h3>Incident Details</h3>
        <table>
            <tr>
                <th>Node</th>
                <th>Interface</th>
                <th>DN</th>
                <th>Delta CRC</th>
                <th>Delta Packets</th>
                <th>CRC %</th>
                <th>Severity</th>
            </tr>
"""

    for inc in incidents:
        sev = inc.get("severity", "unknown")
        sev_class = f"severity-{sev}"
        html += f"""
            <tr>
                <td>{inc.get('node', '')}</td>
                <td>{inc.get('interface_id', '')}</td>
                <td style="font-size: 11px;">{inc.get('dn', '')}</td>
                <td>{inc.get('delta_crc', '')}</td>
                <td>{inc.get('delta_pkts', '')}</td>
                <td>{inc.get('crc_percent_display', '')}</td>
                <td class="{sev_class}">{sev.upper()}</td>
            </tr>
"""

    html += f"""
        </table>

        <div class="footer">
            <p>This is an automated alert from the CRC Error Monitoring System.</p>
            <p>Do not reply to this email.</p>
        </div>
    </body>
    </html>
"""
    return html


def send_email(subject: str, html_body: str, recipients: List[str]) -> dict:
    """
    Send email via SMTP relay (no authentication).

    Uses SMTP_IP for connection (direct IP) with SMTP_HOST as fallback.
    """
    result = {"sent": 0, "failed": 0, "errors": []}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(html_body, "html"))

    try:
        # Connect using IP address directly (no auth required)
        logger.info(f"Connecting to SMTP server {SMTP_IP}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_IP, SMTP_PORT, timeout=30) as server:
            server.ehlo(SMTP_HOST)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
            result["sent"] = len(recipients)
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
    except smtplib.SMTPException as e:
        result["failed"] = len(recipients)
        result["errors"].append(str(e))
        logger.error(f"SMTP error sending email: {e}")
    except Exception as e:
        result["failed"] = len(recipients)
        result["errors"].append(str(e))
        logger.error(f"Error sending email: {e}")

    return result


@activity.defn
async def send_email_notification_activity(input: EmailInput) -> EmailOutput:
    """Temporal activity to send email notifications for CRC incidents."""
    logger.info(f"Starting email notification activity for {input.ip}")
    logger.info(f"Incidents to notify: {len(input.incidents)}")
    logger.info(f"Recipients: {EMAIL_RECIPIENTS}")

    if not input.incidents:
        logger.info("No incidents to report. Skipping email notification.")
        return EmailOutput(emails_sent=0, emails_failed=0, recipients=[])

    if not EMAIL_RECIPIENTS:
        logger.warning("No email recipients configured. Skipping email notification.")
        return EmailOutput(emails_sent=0, emails_failed=0, recipients=[])

    # Build email content
    subject = f"[CRC Alert] {len(input.incidents)} incident(s) detected on {input.ip}"
    html_body = build_incident_email(
        ip=input.ip,
        poll_id=input.poll_id,
        incidents=input.incidents,
        total_interfaces=input.total_interfaces,
    )

    # Send email
    result = send_email(subject, html_body, EMAIL_RECIPIENTS)

    output = EmailOutput(
        emails_sent=result["sent"],
        emails_failed=result["failed"],
        recipients=EMAIL_RECIPIENTS,
    )

    logger.info(f"Email notification complete: sent={output.emails_sent}, failed={output.emails_failed}")
    return output
