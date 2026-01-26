"""
Delta calculation activity for computing CRC error deltas between polls.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List
from temporalio import activity

from .mongodb import get_history_collection
from .logger import delta_logger as logger


@dataclass
class DeltaAnalytics:
    """Analytics data for delta calculation activity."""
    total_interfaces: int = 0
    interfaces_with_history: int = 0
    interfaces_without_history: int = 0
    interfaces_with_positive_delta_crc: int = 0
    interfaces_with_positive_delta_pkts: int = 0
    interfaces_with_zero_delta: int = 0
    no_history_interfaces: List[str] = field(default_factory=list)


@dataclass
class DeltaInput:
    ip: str
    poll_id: str
    protocol: str = "https"


@dataclass
class DeltaOutput:
    deltas: dict
    ip: str
    protocol: str
    analytics: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def calculate_delta_activity(input: DeltaInput) -> DeltaOutput:
    logger.info(f"Starting delta calculation activity for {input.ip}")
    logger.info("=" * 60)
    logger.info(f"Current poll_id: {input.poll_id}")

    # Analytics tracking
    analytics = DeltaAnalytics()

    # Get MongoDB collection
    collection = get_history_collection()
    logger.info(f"Connected to MongoDB collection: {collection.name}")

    # Get current poll data (T1)
    current_poll = list(collection.find({
        "ip": input.ip,
        "poll_id": input.poll_id
    }))

    if not current_poll:
        logger.warning(f"No data found for current poll_id: {input.poll_id}")
        return DeltaOutput(
            deltas={},
            ip=input.ip,
            protocol=input.protocol,
            analytics={"error": "No current poll data found"}
        )

    analytics.total_interfaces = len(current_poll)
    logger.info(f"Found {analytics.total_interfaces} interfaces in current poll")

    # Calculate deltas for each interface (nested by node)
    deltas = {}

    for current in current_poll:
        iface_id = current["interface_id"]
        node = current.get("node", "")
        admin_st = current.get("adminSt", "unknown")

        # Get previous poll for this interface on same node (exclude current poll, get most recent)
        previous = collection.find_one(
            {
                "ip": input.ip,
                "interface_id": iface_id,
                "node": node,  # Include node to match same interface on same node
                "poll_id": {"$ne": input.poll_id}
            },
            sort=[("timestamp", -1)]
        )

        # Initialize node in deltas if not present
        if node not in deltas:
            deltas[node] = {}

        if previous:
            analytics.interfaces_with_history += 1

            # Calculate deltas
            crc_t0 = previous.get("crc_errors", 0)
            crc_t1 = current.get("crc_errors", 0)
            pkts_t0 = previous.get("pkts_cum", 0)
            pkts_t1 = current.get("pkts_cum", 0)

            delta_crc = crc_t1 - crc_t0
            delta_pkts = pkts_t1 - pkts_t0

            # Calculate CRC percentage
            if delta_pkts > 0:
                crc_percent = delta_crc / delta_pkts
            else:
                crc_percent = 0.0

            # Track analytics
            if delta_crc > 0:
                analytics.interfaces_with_positive_delta_crc += 1
            if delta_pkts > 0:
                analytics.interfaces_with_positive_delta_pkts += 1
            if delta_crc == 0 and delta_pkts == 0:
                analytics.interfaces_with_zero_delta += 1

            deltas[node][iface_id] = {
                "dn": current.get("dn", ""),
                "adminSt": admin_st,
                "crc_t0": crc_t0,
                "crc_t1": crc_t1,
                "pkts_t0": pkts_t0,
                "pkts_t1": pkts_t1,
                "delta_crc": delta_crc,
                "delta_pkts": delta_pkts,
                "crc_percent": crc_percent
            }

            logger.debug(
                f"Interface {node}/{iface_id}: DELTA_CRC={delta_crc}, DELTA_PKTS={delta_pkts}, "
                f"CRC_PERCENT={crc_percent:.6f}"
            )
        else:
            analytics.interfaces_without_history += 1
            analytics.no_history_interfaces.append(f"{node}/{iface_id}")

            # First poll - no delta available
            deltas[node][iface_id] = {
                "dn": current.get("dn", ""),
                "adminSt": admin_st,
                "crc_t0": None,
                "crc_t1": current.get("crc_errors", 0),
                "pkts_t0": None,
                "pkts_t1": current.get("pkts_cum", 0),
                "delta_crc": None,
                "delta_pkts": None,
                "crc_percent": None,
                "first_poll": True
            }

            logger.debug(f"Interface {node}/{iface_id}: First poll, no history available")

    # Log analytics summary
    logger.info("=" * 60)
    logger.info("ANALYTICS SUMMARY - Delta Calculation Activity")
    logger.info("=" * 60)
    logger.info(f"Total interfaces: {analytics.total_interfaces}")
    logger.info(f"Interfaces with history: {analytics.interfaces_with_history}")
    logger.info(f"Interfaces without history (first poll): {analytics.interfaces_without_history}")
    logger.info(f"Interfaces with positive DELTA_CRC: {analytics.interfaces_with_positive_delta_crc}")
    logger.info(f"Interfaces with positive DELTA_PKTS: {analytics.interfaces_with_positive_delta_pkts}")
    logger.info(f"Interfaces with zero delta: {analytics.interfaces_with_zero_delta}")
    if analytics.no_history_interfaces:
        logger.info(f"No history interfaces: {analytics.no_history_interfaces}")
    logger.info("=" * 60)

    # Convert analytics to dict
    analytics_dict = {
        "total_interfaces": analytics.total_interfaces,
        "interfaces_with_history": analytics.interfaces_with_history,
        "interfaces_without_history": analytics.interfaces_without_history,
        "interfaces_with_positive_delta_crc": analytics.interfaces_with_positive_delta_crc,
        "interfaces_with_positive_delta_pkts": analytics.interfaces_with_positive_delta_pkts,
        "interfaces_with_zero_delta": analytics.interfaces_with_zero_delta,
        "no_history_interfaces": analytics.no_history_interfaces
    }

    total_interfaces = sum(len(ifaces) for ifaces in deltas.values())
    logger.info(f"Completed. Calculated deltas for {total_interfaces} interfaces across {len(deltas)} nodes")

    return DeltaOutput(
        deltas=deltas,
        ip=input.ip,
        protocol=input.protocol,
        analytics=analytics_dict
    )
