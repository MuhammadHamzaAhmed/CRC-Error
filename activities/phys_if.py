import re
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any
from temporalio import activity

from .session import session
from .logger import phys_if_logger as logger


@dataclass
class PhysIfAnalytics:
    """Analytics data for physical interface activity."""
    total_nodes: int = 0
    total_interfaces: int = 0
    total_admin_up: int = 0
    total_admin_down: int = 0
    empty_nodes: List[str] = field(default_factory=list)  # UUIDs where node extraction failed


@dataclass
class PhysIfInput:
    ip: str
    protocol: str = "https"


@dataclass
class PhysIfOutput:
    interfaces: dict
    ip: str
    protocol: str
    analytics: Dict[str, Any] = field(default_factory=dict)


def extract_node_from_dn(dn: str) -> str:
    """
    Extract node identifier from DN string.
    Example DN: topology/pod-1/node-103/sys/phys-[eth1/33]
    Returns: node-103 or empty string if not found
    """
    match = re.search(r'(node-\d+)', dn)
    if match:
        return match.group(1)
    return ""


@activity.defn
async def get_phys_if_activity(input: PhysIfInput) -> PhysIfOutput:
    logger.info(f"Starting physical interface activity for {input.ip}")
    logger.info("=" * 60)

    url = f"{input.protocol}://{input.ip}/api/node/class/l1PhysIf.json?rsp-subtree=full&rsp-subtree-class=rmonEtherStats"

    logger.debug(f"Request URL: {url}")
    logger.info("Fetching physical interfaces...")

    response = session.get(url)
    logger.debug(f"Response status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    interfaces = {}

    # Analytics tracking
    analytics = PhysIfAnalytics()
    nodes_seen = set()

    imdata = data.get("imdata", [])
    logger.info(f"Processing {len(imdata)} interface records...")

    for item in imdata:
        phys_if = item.get("l1PhysIf", {})
        attrs = phys_if.get("attributes", {})
        dn = attrs.get("dn", "")
        iface_id = attrs.get("id", "")
        admin_st = attrs.get("adminSt", "unknown")

        # Extract node from DN
        node = extract_node_from_dn(dn)

        # Track analytics
        if node:
            nodes_seen.add(node)
            logger.debug(f"Extracted node '{node}' from DN: {dn}")
        else:
            # Generate UUID for tracking empty node extraction
            empty_uuid = str(uuid.uuid4())
            analytics.empty_nodes.append(empty_uuid)
            logger.warning(f"Failed to extract node from DN: {dn} (tracking UUID: {empty_uuid})")

        # Track admin status
        if admin_st == "up":
            analytics.total_admin_up += 1
            logger.debug(f"Interface {iface_id}: adminSt=up")
        else:
            analytics.total_admin_down += 1
            logger.debug(f"Interface {iface_id}: adminSt={admin_st}")

        # Extract CRC errors from rmonEtherStats
        crc_errors = 0
        children = phys_if.get("children", [])
        for child in children:
            rmon = child.get("rmonEtherStats", {})
            rmon_attrs = rmon.get("attributes", {})
            crc_errors = int(rmon_attrs.get("cRCAlignErrors", 0))

        # Store interface nested under node to avoid duplicate interface names overwriting
        # Structure: interfaces[node][iface_id] = {...}
        if node not in interfaces:
            interfaces[node] = {}
        interfaces[node][iface_id] = {
            "dn": dn,
            "adminSt": admin_st,
            "crc_errors": crc_errors
        }
        logger.debug(f"Interface {node}/{iface_id}: adminSt={admin_st}, CRC errors={crc_errors}")

    # Finalize analytics
    analytics.total_nodes = len(nodes_seen)
    # Count total interfaces across all nodes
    analytics.total_interfaces = sum(len(ifaces) for ifaces in interfaces.values())

    # Log analytics summary
    logger.info("=" * 60)
    logger.info("ANALYTICS SUMMARY - Physical Interface Activity")
    logger.info("=" * 60)
    logger.info(f"Total nodes extracted: {analytics.total_nodes}")
    logger.info(f"Total interfaces: {analytics.total_interfaces}")
    logger.info(f"Total adminSt=up: {analytics.total_admin_up}")
    logger.info(f"Total adminSt=down/other: {analytics.total_admin_down}")
    logger.info(f"Empty node extractions: {len(analytics.empty_nodes)}")
    if analytics.empty_nodes:
        logger.warning(f"UUIDs with empty node: {analytics.empty_nodes}")
    logger.info("=" * 60)

    # Convert analytics to dict for output
    analytics_dict = {
        "total_nodes": analytics.total_nodes,
        "total_interfaces": analytics.total_interfaces,
        "total_admin_up": analytics.total_admin_up,
        "total_admin_down": analytics.total_admin_down,
        "empty_nodes": analytics.empty_nodes
    }

    logger.info(f"Completed. Found {analytics.total_interfaces} interfaces across {analytics.total_nodes} nodes")

    return PhysIfOutput(
        interfaces=interfaces,
        ip=input.ip,
        protocol=input.protocol,
        analytics=analytics_dict
    )
