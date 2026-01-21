import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

from workflow import CrcErrorWorkflow
from activities import (
    login_activity,
    get_phys_if_activity,
    get_ingr_total_activity,
    store_history_activity,
    calculate_delta_activity,
    evaluate_incident_activity,
)
from props import TEMPORAL_QUEUE


async def main():
    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)

    worker = Worker(
        client,
        task_queue=TEMPORAL_QUEUE,
        workflows=[CrcErrorWorkflow],
        activities=[
            login_activity,
            get_phys_if_activity,
            get_ingr_total_activity,
            store_history_activity,
            calculate_delta_activity,
            evaluate_incident_activity,
        ],
    )

    print(f"Starting worker on queue: {TEMPORAL_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
