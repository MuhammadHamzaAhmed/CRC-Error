import os
from dataclasses import dataclass
from temporalio import activity

from .session import session
from .logger import login_logger as logger


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
    logger.info(f"Starting login activity for {input.ip}")
    url = f"{input.protocol}://{input.ip}/api/aaaLogin.json"
    username = os.environ.get("ACI_USERNAME")
    password = os.environ.get("ACI_PASSWORD")

    logger.debug(f"Login URL: {url}")
    logger.debug(f"Username: {username}")

    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }

    logger.info("Sending login request...")
    response = session.post(url, json=payload)
    logger.debug(f"Response status code: {response.status_code}")

    if response.status_code != 200:
        logger.error(f"Login failed with status code: {response.status_code}")
        logger.error(f"Response body: {response.text}")
        raise Exception(f"Login failed with status code: {response.status_code}")

    logger.info(f"Login successful for {input.ip}")
    return LoginOutput(ip=input.ip, protocol=input.protocol)
