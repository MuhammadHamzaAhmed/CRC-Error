import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

from workflow import CrcErrorWorkflow
from activities import login_activity, get_phys_if_activity, get_ingr_total_activity


def load_properties(file_path: str) -> dict:
    props = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props


async def main():
    props = load_properties("config.properties")
    queue_name = props.get("TEMPORAL_QUEUE", "crc-error-queue")

    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)

    worker = Worker(
        client,
        task_queue=queue_name,
        workflows=[CrcErrorWorkflow],
        activities=[login_activity, get_phys_if_activity, get_ingr_total_activity],
    )

    print(f"Starting worker on queue: {queue_name}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
