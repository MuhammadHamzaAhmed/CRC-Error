"""
Store history activity for saving interface data to MongoDB.
"""
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List
from temporalio import activity

from .mongodb import get_history_collection, get_current_time
from .logger import store_history_logger as logger


@dataclass
class StoreHistoryAnalytics:
    """Analytics data for store history activity."""
    total_interfaces: int = 0
    records_inserted: int = 0
    records_failed: int = 0
    failed_interfaces: List[str] = field(default_factory=list)


@dataclass
class StoreHistoryInput:
    ip: str
    interfaces: dict
    protocol: str = "https"


@dataclass
class StoreHistoryOutput:
    poll_id: str
    ip: str
    protocol: str
    records_stored: int
    analytics: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def store_history_activity(input: StoreHistoryInput) -> StoreHistoryOutput:
    logger.info(f"Starting store history activity for {input.ip}")
    logger.info("=" * 60)

    # Generate unique poll ID for this batch
    poll_id = str(uuid.uuid4())
    timestamp = get_current_time()

    logger.info(f"Poll ID: {poll_id}")
    logger.info(f"Timestamp: {timestamp}")

    # Analytics tracking
    analytics = StoreHistoryAnalytics()
    # Count total interfaces across all nodes
    analytics.total_interfaces = sum(len(ifaces) for ifaces in input.interfaces.values())

    # Get MongoDB collection
    collection = get_history_collection()
    logger.info(f"Connected to MongoDB collection: {collection.name}")

    # Prepare documents for insertion (iterate through nested node->interfaces structure)
    documents = []
    for node, node_interfaces in input.interfaces.items():
        for iface_id, iface_data in node_interfaces.items():
            doc = {
                "poll_id": poll_id,
                "timestamp": timestamp,
                "ip": input.ip,
                "interface_id": iface_id,
                "node": node,
                "dn": iface_data.get("dn", ""),
                "adminSt": iface_data.get("adminSt", "unknown"),
                "crc_errors": iface_data.get("crc_errors", 0),
                "pkts_cum": iface_data.get("pkts_cum", 0)
            }
            documents.append(doc)
            logger.debug(f"Prepared document for interface {node}/{iface_id}: CRC={doc['crc_errors']}, PKTS={doc['pkts_cum']}")

    # Insert documents
    if documents:
        try:
            result = collection.insert_many(documents)
            analytics.records_inserted = len(result.inserted_ids)
            logger.info(f"Successfully inserted {analytics.records_inserted} records")
        except Exception as e:
            logger.error(f"Failed to insert documents: {str(e)}")
            analytics.records_failed = len(documents)
            for doc in documents:
                analytics.failed_interfaces.append(doc["interface_id"])

    # Log analytics summary
    logger.info("=" * 60)
    logger.info("ANALYTICS SUMMARY - Store History Activity")
    logger.info("=" * 60)
    logger.info(f"Poll ID: {poll_id}")
    logger.info(f"Total interfaces: {analytics.total_interfaces}")
    logger.info(f"Records inserted: {analytics.records_inserted}")
    logger.info(f"Records failed: {analytics.records_failed}")
    if analytics.failed_interfaces:
        logger.warning(f"Failed interfaces: {analytics.failed_interfaces}")
    logger.info("=" * 60)

    # Convert analytics to dict
    analytics_dict = {
        "poll_id": poll_id,
        "timestamp": str(timestamp),
        "total_interfaces": analytics.total_interfaces,
        "records_inserted": analytics.records_inserted,
        "records_failed": analytics.records_failed,
        "failed_interfaces": analytics.failed_interfaces
    }

    logger.info(f"Completed. Stored {analytics.records_inserted} records with poll_id: {poll_id}")

    return StoreHistoryOutput(
        poll_id=poll_id,
        ip=input.ip,
        protocol=input.protocol,
        records_stored=analytics.records_inserted,
        analytics=analytics_dict
    )
