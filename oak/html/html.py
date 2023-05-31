from gettext import GNUTranslations
from pathlib import Path
from shutil import copy

from jinja2 import Environment

from oak.model import Data


RESOURCES_DIR = Path("./oak/html/resources")


def render_html(build_dir: Path, data: Data, job_title: str, translations: GNUTranslations) -> Path:
    env = Environment(extensions=['jinja2.ext.i18n'])
    env.install_gettext_translations(translations)

    template = env.from_string((RESOURCES_DIR / "index.html").read_text())
    rendered = template.render(data=data, job_title=job_title)

    html_dir = build_dir / "html" / translations.info()["language"]
    html_dir.mkdir(exist_ok=True, parents=True)

    for f in ["style.css", "sulim.jpg"]:
        copy(RESOURCES_DIR / f, html_dir / f)

    html_rendered = html_dir / "index.html"
    html_rendered.write_text(rendered)

    return html_dir
