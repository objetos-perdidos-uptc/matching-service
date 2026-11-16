from enum import Enum
from dataclasses import dataclass

# Create Enum for report type
class ReportType(Enum):
    LOST = "LOST"
    FOUND = "FOUND"

# creating Location class inmutable
@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
