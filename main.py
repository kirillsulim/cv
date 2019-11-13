from typing import Dict, List
from dataclasses import dataclass, field
from datetime import date
import yaml

import pprint

from pylatex import Document, Section, Subsection, Command
from pylatex.utils import italic, NoEscape


@dataclass
class Personal(yaml.YAMLObject):
    yaml_tag = '!Personal'

    name: Dict[str, str] = None
    surname: Dict[str, str] = None
    phone: str = None
    email: str = None
    github: str = None
    site: str = None


@dataclass
class Education(yaml.YAMLObject):
    yaml_tag = '!Education'

    from_date: date = None
    to_date: date = None
    university: Dict[str, str] = None
    faculty: Dict[str, str] = None
    speciality: Dict[str, str] = None


@dataclass
class Organisation(yaml.YAMLObject):
    yaml_tag = '!Organisation'

    name: Dict[str, str] = None


@dataclass
class WorkExperience(yaml.YAMLObject):
    yaml_tag = '!WorkExperience'

    from_date: date = None
    to_date: date = None
    organisation: Organisation = None
    position: Dict[str, str] = None
    bullets: List[Dict[str, str]] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


@dataclass
class Data(yaml.YAMLObject):
    yaml_tag = '!Data'

    personal: Personal = None
    education: List[Education] = field(default_factory=list)
    work_experience: List[WorkExperience] = field(default_factory=list)


with open('data.yaml', 'r') as f:
    data: Data = yaml.load(f, Loader=yaml.Loader)

doc = Document('basic')

with doc.create(Section('A section')):
    doc.append('Some regular text and some ')
    doc.append(italic('italic text. '))

    with doc.create(Subsection('A subsection')):
        doc.append('Also some crazy characters: $&#{}')

doc.generate_pdf('cv.pdf')