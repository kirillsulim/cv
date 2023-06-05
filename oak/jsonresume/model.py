from dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass
class Location:
    address: Optional[str]
    postalCode: Optional[str]
    city: Optional[str]
    countryCode: Optional[str]
    region: Optional[str]


@dataclass
class Profile:
    network: str
    url: str
    username: Optional[str]


@dataclass
class Basics:
    name: Optional[str]
    label: Optional[str]
    image: Optional[str]
    phone: Optional[str]
    url: Optional[str]
    summary: Optional[str]
    location: Optional[Location]
    profiles: List[Profile]


@dataclass
class Work:
    name: str  # Some templates wants name as a company name
    company: str  # Most of the templates wants company as company name
    position: str
    url: Optional[str]
    startDate: date
    endDate: Optional[date]
    summary: Optional[str]
    highlights: List[str]


@dataclass
class Education:
    institution: str
    url: Optional[str]
    area: str
    studyType: str
    startDate: date
    endDate: Optional[date]
    score: Optional[str]
    courses: List[str]


@dataclass
class JsonResume:
    basics: Basics
    work: List[Work]
    education: List[Education]
