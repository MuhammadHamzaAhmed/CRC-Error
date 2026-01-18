import re
from dataclasses import dataclass
from temporalio import activity

from .session import session


@dataclass
class IngrTotalInput:
    ip: str
    interfaces: dict


@activity.defn
async def get_ingr_total_activity(input: IngrTotalInput) -> dict:
    url = f"https://{input.ip}/api/class/eqptIngrTotal15min.json"

    response = session.get(url)
    response.raise_for_status()

    data = response.json()
    ingr_data = {}

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

    result = {}
    for iface_id, iface_data in input.interfaces.items():
        result[iface_id] = iface_data.copy()
        if iface_id in ingr_data:
            result[iface_id]["pktsRateMin"] = ingr_data[iface_id]["pktsRateMin"]
            result[iface_id]["pktsRateMax"] = ingr_data[iface_id]["pktsRateMax"]

    return result
