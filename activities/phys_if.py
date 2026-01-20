from dataclasses import dataclass
from temporalio import activity

from .session import session
from .logger import phys_if_logger as logger


@dataclass
class PhysIfInput:
    ip: str
    protocol: str = "https"


@dataclass
class PhysIfOutput:
    interfaces: dict
    ip: str
    protocol: str


@activity.defn
async def get_phys_if_activity(input: PhysIfInput) -> PhysIfOutput:
    logger.info(f"Starting physical interface activity for {input.ip}")
    url = f"{input.protocol}://{input.ip}/api/node/class/l1PhysIf.json?rsp-subtree=full&rsp-subtree-class=rmonEtherStats"

    logger.debug(f"Request URL: {url}")
    logger.info("Fetching physical interfaces...")
    response = session.get(url)
    logger.debug(f"Response status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    interfaces = {}

    logger.info(f"Processing {len(data.get('imdata', []))} interfaces...")
    for item in data.get("imdata", []):
        phys_if = item.get("l1PhysIf", {})
        attrs = phys_if.get("attributes", {})
        dn = attrs.get("dn", "")
        iface_id = attrs.get("id", "")

        crc_errors = 0
        children = phys_if.get("children", [])
        for child in children:
            rmon = child.get("rmonEtherStats", {})
            rmon_attrs = rmon.get("attributes", {})
            crc_errors = rmon_attrs.get("cRCAlignErrors", 0)

        interfaces[iface_id] = {
            "dn1": dn,
            "crc_errors": crc_errors
        }
        logger.debug(f"Interface {iface_id}: CRC errors = {crc_errors}")

    logger.info(f"Completed. Found {len(interfaces)} interfaces")
    return PhysIfOutput(interfaces=interfaces, ip=input.ip, protocol=input.protocol)
