from pathlib import Path

from oak_build import task, run

from oak.md.md import render_md
from oak.pdf.pdf import render_pdf
from oak.model import get_data
from oak.translation.translation import (
    compile_translations as _compile_translation,
    update_translations as _update_translation,
    get_translations,
)


BUILD_DIR = Path("./build").resolve()
DATA_FILE = Path("data.yaml").resolve()


@task
def load_data():
    return {
        "result": get_data(DATA_FILE, "ru", set())
    }


@task
def translations():
    return {lang: get_translations(lang) for lang in ("en", "ru")}


@task(depends_on=[load_data, translations])
def md(load_data_result, translations_ru):
    render_md(BUILD_DIR, load_data_result, "test-jt", translations_ru)


@task(depends_on=[load_data, translations])
def pdf(load_data_result, translations_ru):
    render_pdf(BUILD_DIR, load_data_result, "test-jt", translations_ru)


@task
def compile_translation():
    _compile_translation()


@task
def update_translation():
    _update_translation()
