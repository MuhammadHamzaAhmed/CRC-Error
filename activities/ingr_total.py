import re
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any
from temporalio import activity

from .session import session
from .logger import ingr_total_logger as logger


@dataclass
class IngrTotalAnalytics:
    """Analytics data for ingress total activity."""
    total_records: int = 0
    total_interfaces_matched: int = 0
    total_interfaces_unmatched: int = 0
    interfaces_with_pkts: int = 0
    interfaces_without_pkts: int = 0
    empty_interface_extractions: List[str] = field(default_factory=list)  # UUIDs where interface extraction failed


@dataclass
class IngrTotalInput:
    ip: str
    interfaces: dict
    protocol: str = "https"


@dataclass
class IngrTotalOutput:
    interfaces: dict
    ip: str
    protocol: str
    analytics: Dict[str, Any] = field(default_factory=dict)


def extract_interface_from_dn(dn: str) -> str:
    """
    Extract interface identifier from DN string.
    Example DN: topology/pod-2/node-2212/sys/phys-[eth1/33]/CDeqptIngrTotal15min
    Returns: eth1/33 or empty string if not found
    """
    match = re.search(r'\[([^\]]+)\]', dn)
    if match:
        return match.group(1)
    return ""


@activity.defn
async def get_ingr_total_activity(input: IngrTotalInput) -> IngrTotalOutput:
    logger.info(f"Starting ingress total activity for {input.ip}")
    logger.info("=" * 60)

    url = f"{input.protocol}://{input.ip}/api/class/eqptIngrTotal15min.json"

    logger.debug(f"Request URL: {url}")
    logger.info("Fetching ingress total stats...")

    response = session.get(url)
    logger.debug(f"Response status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    ingr_data = {}

    # Analytics tracking
    analytics = IngrTotalAnalytics()

    imdata = data.get("imdata", [])
    analytics.total_records = len(imdata)
    logger.info(f"Processing {analytics.total_records} ingress records...")

    for item in imdata:
        ingr = item.get("eqptIngrTotal15min", {})
        attrs = ingr.get("attributes", {})
        dn = attrs.get("dn", "")

        # Extract interface from DN
        iface = extract_interface_from_dn(dn)

        if iface:
            # Extract pktsCum as the main packet counter
            pkts_cum = attrs.get("pktsCum", "0")

            ingr_data[iface] = {
                "pkts_cum": int(pkts_cum),
                "dn": dn
            }
            logger.debug(f"Interface {iface}: pktsCum={pkts_cum}")
        else:
            # Generate UUID for tracking empty interface extraction
            empty_uuid = str(uuid.uuid4())
            analytics.empty_interface_extractions.append(empty_uuid)
            logger.warning(f"Failed to extract interface from DN: {dn} (tracking UUID: {empty_uuid})")

    # Merge with input interfaces
    result = {}
    for iface_id, iface_data in input.interfaces.items():
        result[iface_id] = iface_data.copy()

        if iface_id in ingr_data:
            result[iface_id]["pkts_cum"] = ingr_data[iface_id]["pkts_cum"]
            analytics.total_interfaces_matched += 1
            analytics.interfaces_with_pkts += 1
            logger.debug(f"Matched interface {iface_id}: pktsCum={ingr_data[iface_id]['pkts_cum']}")
        else:
            # No matching ingress data - set pkts_cum to 0
            result[iface_id]["pkts_cum"] = 0
            analytics.total_interfaces_unmatched += 1
            analytics.interfaces_without_pkts += 1
            logger.debug(f"No ingress data for interface {iface_id}, setting pktsCum=0")

    # Log analytics summary
    logger.info("=" * 60)
    logger.info("ANALYTICS SUMMARY - Ingress Total Activity")
    logger.info("=" * 60)
    logger.info(f"Total ingress records from API: {analytics.total_records}")
    logger.info(f"Interfaces matched with phys_if: {analytics.total_interfaces_matched}")
    logger.info(f"Interfaces unmatched: {analytics.total_interfaces_unmatched}")
    logger.info(f"Interfaces with packet data: {analytics.interfaces_with_pkts}")
    logger.info(f"Interfaces without packet data: {analytics.interfaces_without_pkts}")
    logger.info(f"Empty interface extractions: {len(analytics.empty_interface_extractions)}")
    if analytics.empty_interface_extractions:
        logger.warning(f"UUIDs with empty interface: {analytics.empty_interface_extractions}")
    logger.info("=" * 60)

    # Convert analytics to dict for output
    analytics_dict = {
        "total_records": analytics.total_records,
        "total_interfaces_matched": analytics.total_interfaces_matched,
        "total_interfaces_unmatched": analytics.total_interfaces_unmatched,
        "interfaces_with_pkts": analytics.interfaces_with_pkts,
        "interfaces_without_pkts": analytics.interfaces_without_pkts,
        "empty_interface_extractions": analytics.empty_interface_extractions
    }

    logger.info(f"Completed. Merged data for {len(result)} interfaces")

    return IngrTotalOutput(
        interfaces=result,
        ip=input.ip,
        protocol=input.protocol,
        analytics=analytics_dict
    )
