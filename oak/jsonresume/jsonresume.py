from gettext import GNUTranslations
from pathlib import Path
from json import dumps

from marshmallow_dataclass import class_schema

from oak.jsonresume.converter import convert
from oak.jsonresume.model import JsonResume
from oak.model import Data


JsonResumeSchema = class_schema(JsonResume)


def render_json(build_dir: Path, data: Data, job_title: str, translations: GNUTranslations) -> Path:
    _ = translations.gettext
    lang = translations.info()["language"]

    json_resume = convert(data, job_title)
    text = JsonResumeSchema().dumps(json_resume, indent=4)

    out_dir = build_dir / "jsonresume"
    out_dir.mkdir(exist_ok=True, parents=True)

    cv_suffix = _("CV")
    job_title = job_title.replace(" ", "_")
    json_rendered = out_dir / f"{data.personal.name}_{data.personal.surname}_{job_title}_{cv_suffix}.json"
    json_rendered.write_text(text)

    return json_rendered
