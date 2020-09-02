from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from yaml import load as load_yaml, SafeLoader
from marshmallow_dataclass import class_schema


@dataclass
class Personal:
    name: Dict[str, str]
    surname: Dict[str, str]
    phone: Optional[str] = None
    email: Optional[str] = None
    github: Optional[str] = None
    site: Optional[str] = None
    skype: Optional[str] = None


@dataclass
class Education:
    university: Dict[str, str]
    faculty: Dict[str, str]
    speciality: Dict[str, str]
    from_date: Optional[date] = None
    to_date: Optional[date] = None


@dataclass
class Organisation:
    name: Dict[str, str]


@dataclass
class WorkExperience:
    organisation: Organisation
    position: Dict[str, str]
    bullets: List[Dict[str, str]] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    current: bool = False


@dataclass
class Data:
    personal: Personal = None
    education: List[Education] = field(default_factory=list)
    work_experience: List[WorkExperience] = field(default_factory=list)


def load_data(file: Path) -> Data:
    data_dict = load_yaml(file.read_text(), Loader=SafeLoader)
    return class_schema(Data)().load(data_dict)
