from dataclasses import dataclass, field, is_dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Union, Any, Set
from collections.abc import Iterable

from yaml import load as load_yaml, SafeLoader
from marshmallow_dataclass import class_schema


@dataclass
class MultilangStr:
    ru: str
    en: str


@dataclass
class ProfiledMultilangStr(MultilangStr):
    profiles: Optional[List[str]] = field(default_factory=list)


@dataclass
class ProfiledStr:
    value: str
    profiles: Optional[List[str]] = field(default_factory=list)


@dataclass
class Personal:
    name: Union[str, MultilangStr]
    surname: Union[str, MultilangStr]


@dataclass
class Contacts:
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    github: Optional[str] = None
    site: Optional[str] = None
    skype: Optional[str] = None


@dataclass
class AboutMe:
    text_parts: List[Union[str, ProfiledMultilangStr]]


@dataclass
class Education:
    university: Union[str, MultilangStr]
    faculty: Union[str, MultilangStr]
    speciality: Union[str, MultilangStr]
    from_date: Optional[date] = None
    to_date: Optional[date] = None


@dataclass
class Organisation:
    name: Union[str, MultilangStr]


@dataclass
class WorkExperience:
    organisation: Organisation
    position: Union[str, MultilangStr]
    bullets: List[Union[str, ProfiledMultilangStr]] = field(default_factory=list)
    technologies: List[Union[str, ProfiledStr]] = field(default_factory=list)
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    current: bool = False


@dataclass
class Data:
    personal: Personal = None
    contacts: Optional[Contacts] = None
    about_me: Optional[AboutMe] = None
    education: List[Education] = field(default_factory=list)
    work_experience: List[WorkExperience] = field(default_factory=list)


SUPPORTED_LANGS = [
    "ru",
    "en",
]

def _load_data(file: Path) -> Data:
    data_dict = load_yaml(file.read_text(), Loader=SafeLoader)
    return class_schema(Data)().load(data_dict)


def _is_simple_type(obj: Any) -> bool:
    return obj is None or isinstance(obj, (str, date, bool, int, float))


def _resolve_lang_and_profiled_strings(obj: Any, lang: str, profiles: Set[str]) -> Any:
    print(profiles)
    if _is_simple_type(obj):
        return obj
    elif isinstance(obj, Iterable):
        return obj.__class__(filter(lambda o: o is not None, map(lambda it: _resolve_lang_and_profiled_strings(it, lang, profiles), obj)))
    elif isinstance(obj, ProfiledMultilangStr):
        if not obj.profiles or profiles.intersection(obj.profiles):
            return getattr(obj, lang)
        else:
            return None
    elif isinstance(obj, MultilangStr):
        return getattr(obj, lang)
    elif isinstance(obj, ProfiledStr):
        if not obj.profiles or profiles.intersection(obj.profiles):
            return obj.value
        else:
            return None
    elif isinstance(obj, Contacts):
        return _contacts_preprocessor(obj, profiles)
    elif is_dataclass(obj):
        args = {}
        for k, v in obj.__dict__.items():
            args[k] = _resolve_lang_and_profiled_strings(v, lang, profiles)
        return obj.__class__(**args)
    else:
        raise Exception(f"Unsupported class {obj.__class__}")


def _contacts_preprocessor(contacts: Contacts, profiles: Set[str]) -> Contacts:
    args = {}
    for contact_type, value in contacts.__dict__.items():
        if not f"exclude_{contact_type}" in profiles:
            args[contact_type] = value
    return Contacts(**args)


def get_data(file: Path, lang: str, profiles: Set[str]) -> Data:
    if lang not in SUPPORTED_LANGS:
        raise Exception(f"Unsupported language {lang}. Supported languages are {', '.join(SUPPORTED_LANGS)}.")

    data = _load_data(file)
    preprocessed_data = _resolve_lang_and_profiled_strings(data, lang, profiles)
    return preprocessed_data
