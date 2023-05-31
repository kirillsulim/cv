import sys
import os
import gettext
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy, rmtree
from typing import List, Set
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
from subprocess import run



from jinja2 import Environment

from slugify import slugify

import requests
import pydrive2

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from git import Repo
from github import Github, UnknownObjectException

from model import Data, get_data
from dogebuild import make_mode, task, add_parameter



make_mode()


PROFILES_DICT = {
    "md_for_github": ["exclude_phone"],
    "pdf": [],
    "pdf_teamlead": ["teamlead"],
}


def parse_profiles(value: str):
    result = []
    for profile in map(lambda s: s.strip(" "), value.split(",")):
        if profile not in PROFILES_DICT:
            raise Exception(f"Unknown profile {profile}. Allowed values are {', '.join(PROFILES_DICT.keys())}")
        result.append(set(PROFILES_DICT[profile]))
    return result


def parse_langs(value: str):
    return list(map(lambda s: s.strip(" "), value.split(",")))


add_parameter("data_file", parser=Path, default=Path("./data.yaml").resolve())
add_parameter("job_title")
add_parameter("langs", parser=parse_langs, default=["en", "ru"])
add_parameter("profiles", parser=parse_profiles, default=[])
add_parameter("release_tag")
add_parameter("debug", parser=bool, default=False)

build_dir = Path("./build").resolve()

github_user = "ksbenderbot"
github_token = os.environ["GITHUB_TOKEN"]
git_user_email = "ksbenderbot@ya.ru"
git_user_name = "Bender Rodriguez"


@task
def clean():
    rmtree(build_dir)


@task
def render_html(data_file: Path, job_title: str, langs: str, profiles: List[Set[str]]):
    artifacts = {}
    for lang in langs:
        tr = gettext.translation("messages", localedir="locales", languages=[lang])
        _ = tr.gettext
        for profile in profiles:
            data = get_data(data_file, lang, profile)

            env = Environment(extensions=['jinja2.ext.i18n'])
            env.install_gettext_translations(tr)
            template = env.from_string(Path("./resources/html/index.html").read_text())
            rendered = template.render(data=data, lang=lang, job_title=job_title)

            html_dir = build_dir / "html" / lang
            html_dir.mkdir(exist_ok=True, parents=True)
            copy(Path("./resources/html/style.css"), html_dir / "style.css")
            copy(Path("./resources/html/sulim.jpg"), html_dir / "sulim.jpg")

            html_rendered = html_dir / "index.html"
            html_rendered.write_text(rendered)

            artifacts.setdefault("html", []).append(html_dir)
            artifacts.setdefault(f"html_{lang}", []).append(html_dir)

    return 0, artifacts




    return 0, artifacts


@task(depends=["render_md"])
def commit_md_to_github(debug, md_en):
    if len(md_en) != 1:
        raise Exception(f"Incorrect artifact list md_en {md_en}")

    repo_dir = build_dir / "github"
    repo_dir.mkdir(exist_ok=True, parents=True)

    with TemporaryDirectory(dir=repo_dir) as tmp_dir:
        repo = Repo.clone_from(f"https://{github_user}:{github_token}@github.com/kirillsulim/kirillsulim", tmp_dir, depth=1)
        repo_cv_file = Path(repo.working_tree_dir) / "cv.md"
        copy(md_en[0], repo_cv_file)

        repo.config_writer() \
            .set_value("user", "name", git_user_name) \
            .set_value("user", "email", git_user_email) \
            .release()

        repo.git.add(".")

        if repo.is_dirty():
            repo.git.commit("-m", "Automatic CV update")
            if not debug:
                repo.git.push()


@task(depends=["render_pdf"])
def release_pdf(debug: bool, pdf: List[Path]):
    if len(pdf) == 0:
        raise Exception("No artifacts to release")

    g = Github(github_user, github_token)
    cv_repo = g.get_repo("kirillsulim/cv")

    build_time = datetime.now(timezone.utc)

    sha = Repo(".").head.commit.hexsha
    tag = build_time.strftime("%Y%m%d_%H%M%S")
    cv_repo.create_git_tag(tag, tag, sha, "commit")

    rel_name = datetime.now(timezone.utc).strftime("%Y %b %d %H:%M:%S %Z")
    rel_message = f"CV pdf builded at {rel_name}"

    release = cv_repo.create_git_release(tag, rel_name, rel_message, draft=True)

    for pdf in pdf:
        path = str(pdf)
        name = slugify(pdf.stem) + "." + pdf.suffix
        label = str(pdf.name)
        release.upload_asset(path, name=name, label=label, content_type="application/pdf")

    release.update_release(release.title, release.body, draft=False)
