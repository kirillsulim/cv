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
add_parameter("job_title", default="Java developer")
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
def render_md(data_file: Path, job_title: str, lang: str, profiles: List[str]):
    data = get_data(data_file, lang, set(profiles))

    env = Environment()
    template = env.from_string(Path("./resources/md/template.md").read_text())
    rendered = template.render(data=data, lang=lang, job_title=job_title)

    md_dir = build_dir / "md"
    md_dir.mkdir(exist_ok=True, parents=True)
    md_rendered = md_dir / f"{data.personal.name}_{data.personal.surname}_{CV_TRANSLATION[lang]}.md"
    md_rendered.write_text(rendered)

    return 0, {f"md_{lang}": [md_rendered]}


@task
def render_html(data_file: Path, job_title: str, lang: str, profiles: List[str]):
    data = get_data(data_file, lang, set(profiles))

    env = Environment()
    template = env.from_string(Path("./resources/html/index.html").read_text())
    rendered = template.render(data=data, lang=lang, job_title=job_title)

    html_dir = build_dir / "html" / lang
    html_dir.mkdir(exist_ok=True, parents=True)
    copy(Path("./resources/html/style.css"), html_dir / "style.css")
    copy(Path("./resources/html/sulim.jpg"), html_dir / "sulim.jpg")

    html_rendered = html_dir / "index.html"
    html_rendered.write_text(rendered)

    return 0, {f"html_{lang}": [html_dir]}


@task
def render_pdf(debug: bool, data_file: Path, job_title: str, lang: str, profiles: List[str]):
    data = get_data(data_file, lang, set(profiles))

    doc = Document(
        'basic',
        fontenc=["T2A", "T1"],
    )
    doc.packages.add(Package("babel", options=["main=russian", "english"]))
    doc.packages.add(Package("cmap"))
    doc.packages.add(Package("hyperref"))
    doc.packages.add(Package("erewhon"))

    doc.append(HugeText(bold(f"{data.personal.name} {data.personal.surname}")))
    doc.append(NewLine())
    doc.append(LargeText(job_title))
    doc.append(NewLine())
    doc.append(NewLine())

    doc.append(f"Email: ")
    doc.append(Command("href", [f"mailto:{data.contacts.email}", f"{data.contacts.email}"]))
    doc.append(NewLine())
    doc.append(f"Phone: {data.contacts.phone}")
    doc.append(NewLine())
    doc.append(f"Site: ")
    doc.append(Command("href", [f"{data.contacts.site}", f"{data.contacts.site}"]))
    doc.append(NewLine())
    doc.append(f"Github: ")
    doc.append(Command("href", [f"https://github.com/{data.contacts.github}", f"{data.contacts.github}"]))
    doc.append(NewLine())

    with doc.create(Section('Work experience', numbering=False)):
        for job in reversed(data.work_experience):
            with doc.create(Subsection(f"{job.position} at {job.organisation.name}", numbering=False)):
                doc.append(italic(f"{job.from_date} - {'Present' if job.current else job.to_date}"))

                bullets = Itemize()
                for bullet in job.bullets:
                    bullets.add_item(f"{bullet}".strip("\n"))
                doc.append(bullets)

                if job.technologies:
                    doc.append("Key skills: ")
                    doc.append(italic(escape_latex(", ".join(job.technologies))))

    with doc.create(Section("Education", numbering=False)):
        for education in reversed(data.education):
            with doc.create(Subsection(f"{education.university} - {education.faculty}", numbering=False)):
                doc.append(italic(f"{education.from_date} - {education.to_date}"))
                doc.append(NewLine())
                doc.append(f"{education.speciality}")

    out_dir = build_dir / "pdf"
    out_dir.mkdir(exist_ok=True, parents=True)
    out_file = out_dir / f"{data.personal.name}_{data.personal.surname}_{CV_TRANSLATION[lang]}"
    doc.generate_pdf(str(out_file), clean=not debug, clean_tex=not debug)

    return 0, {f"pdf_{lang}": [out_file]}


@task(depends=["render_md"])
def commit_to_github_kirillsulim(debug, md_en):
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
