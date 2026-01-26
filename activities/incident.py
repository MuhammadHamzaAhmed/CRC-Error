"""
Incident evaluation activity for detecting CRC error incidents.

Incident Rule:
- IF adminSt == "up"
- AND DELTA_PKTS > 0
- AND CRC_PERCENT > 0.01
- THEN OPEN INCIDENT
- ELSE IGNORE
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List
from temporalio import activity

from .logger import incident_logger as logger

# CRC percentage threshold for incident (1%)
CRC_THRESHOLD = 0.01


@dataclass
class IncidentAnalytics:
    """Analytics data for incident evaluation activity."""
    total_interfaces: int = 0
    interfaces_evaluated: int = 0
    interfaces_skipped_admin_down: int = 0
    interfaces_skipped_no_delta: int = 0
    interfaces_skipped_zero_pkts: int = 0
    interfaces_skipped_first_poll: int = 0
    incidents_opened: int = 0
    incidents_ignored: int = 0
    skipped_admin_down_list: List[str] = field(default_factory=list)


@dataclass
class Incident:
    """Incident data structure."""
    interface_id: str
    node: str
    dn: str
    delta_crc: int
    delta_pkts: int
    crc_percent: float
    severity: str = "warning"


@dataclass
class IncidentInput:
    ip: str
    deltas: dict
    protocol: str = "https"


@dataclass
class IncidentOutput:
    incidents: List[Dict[str, Any]]
    ip: str
    protocol: str
    analytics: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def evaluate_incident_activity(input: IncidentInput) -> IncidentOutput:
    logger.info(f"Starting incident evaluation activity for {input.ip}")
    logger.info("=" * 60)
    logger.info(f"CRC Threshold: {CRC_THRESHOLD} ({CRC_THRESHOLD * 100}%)")

    # Analytics tracking
    analytics = IncidentAnalytics()
    # Count total interfaces across all nodes
    analytics.total_interfaces = sum(len(ifaces) for ifaces in input.deltas.values())

    # Incidents list
    incidents = []

    # Iterate through nested node->interfaces structure
    for node, node_interfaces in input.deltas.items():
        for iface_id, delta_data in node_interfaces.items():
            admin_st = delta_data.get("adminSt", "unknown")
            delta_crc = delta_data.get("delta_crc")
            delta_pkts = delta_data.get("delta_pkts")
            crc_percent = delta_data.get("crc_percent")
            first_poll = delta_data.get("first_poll", False)
            dn = delta_data.get("dn", "")

            logger.debug(f"Evaluating interface {node}/{iface_id}: adminSt={admin_st}, delta_crc={delta_crc}, "
                         f"delta_pkts={delta_pkts}, crc_percent={crc_percent}")

            # Skip if first poll (no history)
            if first_poll:
                analytics.interfaces_skipped_first_poll += 1
                logger.debug(f"Interface {node}/{iface_id}: SKIPPED - First poll, no history")
                continue

            # Rule: Ignore interfaces that are admin down
            if admin_st != "up":
                analytics.interfaces_skipped_admin_down += 1
                analytics.skipped_admin_down_list.append(f"{node}/{iface_id}")
                logger.debug(f"Interface {node}/{iface_id}: SKIPPED - adminSt={admin_st} (not up)")
                continue

            # Rule: Ignore when delta values are None
            if delta_crc is None or delta_pkts is None:
                analytics.interfaces_skipped_no_delta += 1
                logger.debug(f"Interface {node}/{iface_id}: SKIPPED - No delta values")
                continue

            # Rule: Ignore when DELTA_PKTS <= 0
            if delta_pkts <= 0:
                analytics.interfaces_skipped_zero_pkts += 1
                logger.debug(f"Interface {node}/{iface_id}: SKIPPED - DELTA_PKTS={delta_pkts} <= 0")
                continue

            # Interface is eligible for evaluation
            analytics.interfaces_evaluated += 1

            # Rule: IF CRC_PERCENT > 0.01 THEN OPEN INCIDENT
            if crc_percent is not None and crc_percent > CRC_THRESHOLD:
                analytics.incidents_opened += 1

                # Determine severity based on CRC percentage
                if crc_percent > 0.10:  # > 10%
                    severity = "critical"
                elif crc_percent > 0.05:  # > 5%
                    severity = "high"
                elif crc_percent > 0.02:  # > 2%
                    severity = "medium"
                else:
                    severity = "warning"

                incident = {
                    "interface_id": iface_id,
                    "node": node,
                    "dn": dn,
                    "delta_crc": delta_crc,
                    "delta_pkts": delta_pkts,
                    "crc_percent": crc_percent,
                    "crc_percent_display": f"{crc_percent * 100:.2f}%",
                    "severity": severity
                }
                incidents.append(incident)

                logger.warning(
                    f"INCIDENT OPENED - Interface {node}/{iface_id}: "
                    f"CRC_PERCENT={crc_percent * 100:.2f}% > {CRC_THRESHOLD * 100}% threshold, "
                    f"severity={severity}"
                )
            else:
                analytics.incidents_ignored += 1
                logger.debug(
                    f"Interface {node}/{iface_id}: NO INCIDENT - CRC_PERCENT={crc_percent * 100:.4f}% <= "
                    f"{CRC_THRESHOLD * 100}% threshold"
                )

    # Log analytics summary
    logger.info("=" * 60)
    logger.info("ANALYTICS SUMMARY - Incident Evaluation Activity")
    logger.info("=" * 60)
    logger.info(f"Total interfaces: {analytics.total_interfaces}")
    logger.info(f"Interfaces evaluated: {analytics.interfaces_evaluated}")
    logger.info(f"Interfaces skipped (admin down): {analytics.interfaces_skipped_admin_down}")
    logger.info(f"Interfaces skipped (first poll): {analytics.interfaces_skipped_first_poll}")
    logger.info(f"Interfaces skipped (no delta): {analytics.interfaces_skipped_no_delta}")
    logger.info(f"Interfaces skipped (zero pkts): {analytics.interfaces_skipped_zero_pkts}")
    logger.info(f"Incidents OPENED: {analytics.incidents_opened}")
    logger.info(f"Incidents ignored: {analytics.incidents_ignored}")
    if analytics.skipped_admin_down_list:
        logger.debug(f"Admin down interfaces: {analytics.skipped_admin_down_list}")
    logger.info("=" * 60)

    # Convert analytics to dict
    analytics_dict = {
        "total_interfaces": analytics.total_interfaces,
        "interfaces_evaluated": analytics.interfaces_evaluated,
        "interfaces_skipped_admin_down": analytics.interfaces_skipped_admin_down,
        "interfaces_skipped_first_poll": analytics.interfaces_skipped_first_poll,
        "interfaces_skipped_no_delta": analytics.interfaces_skipped_no_delta,
        "interfaces_skipped_zero_pkts": analytics.interfaces_skipped_zero_pkts,
        "incidents_opened": analytics.incidents_opened,
        "incidents_ignored": analytics.incidents_ignored,
        "skipped_admin_down_list": analytics.skipped_admin_down_list
    }

    logger.info(f"Completed. Found {len(incidents)} incidents")

    return IncidentOutput(
        incidents=incidents,
        ip=input.ip,
        protocol=input.protocol,
        analytics=analytics_dict
    )
