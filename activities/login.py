import os
from dataclasses import dataclass
from temporalio import activity

from .session import session


@dataclass
class LoginInput:
    ip: str
    protocol: str = "https"


@dataclass
class LoginOutput:
    ip: str
    protocol: str


@activity.defn
async def login_activity(input: LoginInput) -> LoginOutput:
    url = f"{input.protocol}://{input.ip}/api/aaaLogin.json"
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

    return LoginOutput(ip=input.ip, protocol=input.protocol)
