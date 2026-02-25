"""
Centralized configuration properties loaded from environment variables.
"""
import os

# Temporal configuration
TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_QUEUE = "crc-error-queue"
WORKFLOW_NAME = "CrcErrorWorkflow"

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "crc_error")

# Timezone configuration (default: Saudi Arabia Riyadh)
TZ = os.environ.get("TZ", "Asia/Riyadh")

# SMTP Email configuration (no authentication required)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtpdr.alrajhi.bank")
SMTP_IP = os.environ.get("SMTP_IP", "10.242.252.46")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "itopalert@alrajhi.bank")

# Recipient list for incident notifications
EMAIL_RECIPIENTS = [
    "MuAhmed@alrajhibank.com.sa",
]
