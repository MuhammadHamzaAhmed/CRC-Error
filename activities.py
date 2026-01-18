import os
import re
import requests
from dataclasses import dataclass
from temporalio import activity

requests.packages.urllib3.disable_warnings()

session = requests.Session()
session.verify = False


@dataclass
class LoginInput:
    ip: str


@dataclass
class PhysIfInput:
    ip: str


@dataclass
class PhysIfOutput:
    interfaces: dict
    ip: str


@dataclass
class IngrTotalInput:
    ip: str
    interfaces: dict


@activity.defn
async def login_activity(input: LoginInput) -> str:
    url = f"https://{input.ip}/api/aaaLogin.json"
    username = os.environ.get("ACI_USERNAME")
    password = os.environ.get("ACI_PASSWORD")

    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }

    response = session.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Login failed with status code: {response.status_code}")

    return input.ip


@activity.defn
async def get_phys_if_activity(input: PhysIfInput) -> PhysIfOutput:
    url = f"https://{input.ip}/api/node/class/l1PhysIf.json?rsp-subtree=full&rsp-subtree-class=rmonEtherStats"

    response = session.get(url)
    response.raise_for_status()

    data = response.json()
    interfaces = {}

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

    return PhysIfOutput(interfaces=interfaces, ip=input.ip)


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
