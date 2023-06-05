import os

from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree, copy
from typing import FrozenSet

from oak_build import task

from oak.github import (
    commit_md_to_github,
    release_pdf as _release_pdf,
    push_gist,
    GitUserInfo,
    GithubUserCredentials
)
from oak.md.md import render_md
from oak.pdf.pdf import render_pdf
from oak.html.html import render_html
from oak.jsonresume.jsonresume import render_json
from oak.model import get_data
from oak.translation.translation import (
    compile_translations as _compile_translation,
    update_translations as _update_translation,
    get_translations,
)


BUILD_DIR = Path("./build").resolve()
DATA_FILE = Path("data.yaml").resolve()

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
def github_credentials():
    return {
        "result": GithubUserCredentials(
            user="ksbenderbot",
            token=os.environ["GITHUB_TOKEN"],
        )
    }


@task()
def gist_credentials():
    return {
        "result": GithubUserCredentials(
            user="kirillsulim",
            token=os.environ["GIST_TOKEN"],
        )
    }


@task
def git_user():
    return {
        "result": GitUserInfo(
            name="Bender Rodriguez",
            email="ksbenderbot@ya.ru",
        )
    }


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


@task(depends_on=[load_data, translations])
def jsonresume(load_data_result, translations_result):
    result = {}
    for (lang, profile), data in load_data_result.items():
        translations = translations_result[lang]
        _ = translations.gettext

        json_type = f"{lang}_{profile.name}"
        result[json_type] = render_json(BUILD_DIR, data, _(profile.job_title), translations)

    return {
        "result": result,
    }


@task(depends_on=[md, github_credentials, git_user])
def commit_en_md(md_en_java_senior, git_user_result, github_credentials_result):
    commit_md_to_github(md_en_java_senior, git_user_result, github_credentials_result)


@task(depends_on=[pdf, github_credentials])
def release_pdf(pdf_result, github_credentials_result):
    _release_pdf(pdf_result, github_credentials_result)


@task(depends_on=[jsonresume, gist_credentials])
def push_jsonresume_gist(jsonresume_result, gist_credentials_result):
    resume_file = jsonresume_result["en_java_senior"]

    push_gist(resume_file, "522c594d695740bc8bd0e97160305bab", gist_credentials_result)
