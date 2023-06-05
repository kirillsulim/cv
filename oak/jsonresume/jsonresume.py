from gettext import GNUTranslations
from pathlib import Path

from marshmallow import Schema, post_dump
from marshmallow_dataclass import class_schema

from oak.jsonresume.converter import convert
from oak.jsonresume.model import JsonResume
from oak.model import Data


class BaseSchema(Schema):
    class Meta:
        ordered=True

    SKIP_VALUES = [
        lambda v: v is None,
    ]

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items()
            if not any([predicate(value) for predicate in self.SKIP_VALUES])
        }


JsonResumeSchema = class_schema(JsonResume, BaseSchema)


def remove_skip_values(self, data):
    return {
        key: value for key, value in data.items()
        if value is not None
    }


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
