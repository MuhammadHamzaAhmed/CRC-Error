import re
from dataclasses import dataclass
from temporalio import activity

from .session import session
from .logger import ingr_total_logger as logger


@dataclass
class IngrTotalInput:
    ip: str
    interfaces: dict
    protocol: str = "https"


@activity.defn
async def get_ingr_total_activity(input: IngrTotalInput) -> dict:
    logger.info(f"Starting ingress total activity for {input.ip}")
    url = f"{input.protocol}://{input.ip}/api/class/eqptIngrTotal15min.json"

    logger.debug(f"Request URL: {url}")
    logger.info("Fetching ingress total stats...")
    response = session.get(url)
    logger.debug(f"Response status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    ingr_data = {}

    logger.info(f"Processing {len(data.get('imdata', []))} ingress records...")
    for item in data.get("imdata", []):
        ingr = item.get("eqptIngrTotal15min", {})
        attrs = ingr.get("attributes", {})
        dn = attrs.get("dn", "")

        match = re.search(r'\[([^\]]+)\]', dn)
        if match:
            iface = match.group(1)
            ingr_data[iface] = {
                "pktsRateMin": attrs.get("pktsRateMin", "0"),
                "pktsRateMax": attrs.get("pktsRateMax", "0")
            }
            logger.debug(f"Interface {iface}: pktsRateMin={ingr_data[iface]['pktsRateMin']}, pktsRateMax={ingr_data[iface]['pktsRateMax']}")

    result = {}
    for iface_id, iface_data in input.interfaces.items():
        result[iface_id] = iface_data.copy()
        if iface_id in ingr_data:
            result[iface_id]["pktsRateMin"] = ingr_data[iface_id]["pktsRateMin"]
            result[iface_id]["pktsRateMax"] = ingr_data[iface_id]["pktsRateMax"]

    logger.info(f"Completed. Merged data for {len(result)} interfaces")
    return result
