from gettext import GNUTranslations
from typing import Callable

from jinja2 import Environment

from ..model import *


def render_md(build_dir: Path, data: Data, job_title: str, translations: GNUTranslations) -> Path:
    _ = translations.gettext

    env = Environment(extensions=['jinja2.ext.i18n'])
    env.install_gettext_translations(translations, newstyle=True)
    env.policies["ext.i18n.trimmed"] = True

    template = env.from_string(Path("./oak/md/resources/template.md").read_text())
    rendered = template.render(data=data, job_title=job_title)

    md_dir = build_dir / "md"
    md_dir.mkdir(exist_ok=True, parents=True)
    cv_suffix = _("CV")
    md_rendered = md_dir / f"{data.personal.name}_{data.personal.surname}_{cv_suffix}.md"
    md_rendered.write_text(rendered)

    return md_rendered
