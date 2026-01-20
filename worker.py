import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

from workflow import CrcErrorWorkflow
from activities import login_activity, get_phys_if_activity, get_ingr_total_activity
from activities.logger import worker_logger as logger
from props import TEMPORAL_QUEUE


async def main():
    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    logger.info(f"Connecting to Temporal server at {temporal_host}")

    try:
        client = await Client.connect(temporal_host)
        logger.info("Successfully connected to Temporal server")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {e}")
        raise

    worker = Worker(
        client,
        task_queue=TEMPORAL_QUEUE,
        workflows=[CrcErrorWorkflow],
        activities=[login_activity, get_phys_if_activity, get_ingr_total_activity],
    )

    logger.info(f"Starting worker on queue: {TEMPORAL_QUEUE}")
    logger.info(f"Registered workflows: [CrcErrorWorkflow]")
    logger.info(f"Registered activities: [login_activity, get_phys_if_activity, get_ingr_total_activity]")

    try:
        await worker.run()
    except Exception as e:
        logger.error(f"Worker stopped with error: {e}")
        raise
    finally:
        logger.info("Worker shut down")


if __name__ == "__main__":
    asyncio.run(main())
