import sys
import os
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy
from typing import List
from tempfile import TemporaryDirectory

from pylatex import Document, Section, Subsection, Package
from pylatex.base_classes import Command
from pylatex.basic import HugeText, NewLine, LargeText
from pylatex.utils import italic, bold, escape_latex
from pylatex.lists import Itemize

from jinja2 import Environment

import requests
import pydrive2

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from git import Repo

from model import Data, get_data
from dogebuild import make_mode, task, add_parameter



make_mode()


def parse_profiles(value: str):
    return list(map(lambda s: s.strip(" "), value.split(",")))


add_parameter("data_file", parser=Path, default=Path("./data.yaml").resolve())
add_parameter("lang", default="en")
add_parameter("profiles", parser=parse_profiles, default=[])
add_parameter("debug", parser=bool, default=False)

build_dir = Path("./build").resolve()

github_user = "ksbenderbot"
github_token = os.environ["GITHUB_TOKEN"]
git_user_email = "ksbenderbot@ya.ru"
git_user_name = "Bender Rodriguez"


CV_TRANSLATION = {
    "en": "CV",
    "ru": "Резюме",
}


@task
def render_md(data_file: Path, lang: str, profiles: List[str]):
    data = get_data(data_file, lang, set(profiles))

    env = Environment()
    template = env.from_string(Path("./resources/md/template.md").read_text())
    rendered = template.render(data=data, lang=lang, job_title="Java developer")

    md_dir = build_dir / "md"
    md_dir.mkdir(exist_ok=True, parents=True)
    md_rendered = md_dir / f"{data.personal.name}_{data.personal.surname}_{CV_TRANSLATION[lang]}.md"
    md_rendered.write_text(rendered)

    return 0, {f"md_{lang}": [md_rendered]}


@task(depends=["render_md"])
def upload_to_github(debug, md_en):
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
