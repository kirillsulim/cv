import os

from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import FrozenSet

from oak_build import task, run

from oak.github import (
    commit_md_to_github,
    release_pdf as _release_pdf,
    GitUserInfo,
    GithubUserCredentials
)
from oak.md.md import render_md
from oak.pdf.pdf import render_pdf
from oak.html.html import render_html
from oak.model import get_data
from oak.translation.translation import (
    compile_translations as _compile_translation,
    update_translations as _update_translation,
    get_translations,
)


BUILD_DIR = Path("./build").resolve()
DATA_FILE = Path("data.yaml").resolve()

GITHUB_CREDENTIALS = GithubUserCredentials(
    user="ksbenderbot",
    token=os.environ["GITHUB_TOKEN"],
)
GIT_USER = GitUserInfo(
    name="Bender Rodriguez",
    email="ksbenderbot@ya.ru",
)


LANGS = [
    "en",
    "ru",
]


@dataclass(eq=True, frozen=True)
class Profile:
    name: str
    job_title: str
    render_profiles: FrozenSet[str]


PROFILES = [
    Profile(
        name="teamlead",
        job_title="Team Lead",
        render_profiles=frozenset([
            "teamlead",
        ])
    ),
    Profile(
        name="java_senior",
        job_title="Senior Java Developer",
        render_profiles=frozenset([
            "java_senior",
        ])
    ),
]


@task
def clean():
    rmtree(BUILD_DIR)


@task
def compile_translation():
    _compile_translation()


@task
def update_translation():
    _update_translation()


@task(depends_on=[compile_translation])
def translations():
    return {
        "result": {lang: get_translations(lang) for lang in ("en", "ru")}
    }


@task
def load_data():
    result = {}
    for lang in LANGS:
        for profile in PROFILES:
            result[(lang, profile)] = get_data(DATA_FILE, lang, profile.render_profiles)
    return {
        "result": result
    }


@task(depends_on=[load_data, translations])
def md(load_data_result, translations_result):
    result = {}
    for (lang, profile), data in load_data_result.items():
        translations = translations_result[lang]
        _ = translations.gettext

        md_type = f"{lang}_{profile.name}"
        result[md_type] = render_md(BUILD_DIR, data, _(profile.job_title), translations)

    return result


@task(depends_on=[load_data, translations])
def pdf(load_data_result, translations_result):
    result = []
    for (lang, profile), data in load_data_result.items():
        translations = translations_result[lang]
        _ = translations.gettext

        result.append(render_pdf(BUILD_DIR, data, _(profile.job_title), translations))

    return {
        "result": result,
    }


@task(depends_on=[load_data, translations])
def html(load_data_result, translations_ru):
    render_html(BUILD_DIR, load_data_result, "test-jt", translations_ru)


@task(depends_on=[md])
def commit_en_md(md_en_java_senior):
    commit_md_to_github(md_en_java_senior, GIT_USER, GITHUB_CREDENTIALS)


@task(depends_on=[pdf])
def release_pdf(pdf_result):
    _release_pdf(pdf_result, GITHUB_CREDENTIALS)
