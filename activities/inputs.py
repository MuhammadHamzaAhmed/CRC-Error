from dataclasses import dataclass


@dataclass
class WorkflowInput:
    """JSON input for the CRC Error workflow."""
    ip: str
