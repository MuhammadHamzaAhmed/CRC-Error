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

# ACI credentials
ACI_USERNAME = os.environ.get("ACI_USERNAME")
ACI_PASSWORD = os.environ.get("ACI_PASSWORD")
