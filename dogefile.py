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

from pylatex import Document, Section, Subsection, Package
from pylatex.base_classes import Command
from pylatex.basic import HugeText, NewLine, LargeText
from pylatex.utils import italic, bold, escape_latex
from pylatex.lists import Itemize

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
def render_md(data_file: Path, job_title: str, langs: str, profiles: List[Set[str]]):
    artifacts = {}
    for lang in langs:
        for profile in profiles:
            data = get_data(data_file, lang, profile)

            env = Environment()
            template = env.from_string(Path("./resources/md/template.md").read_text())
            rendered = template.render(data=data, lang=lang, job_title=job_title)

            md_dir = build_dir / "md"
            md_dir.mkdir(exist_ok=True, parents=True)
            md_rendered = md_dir / f"{data.personal.name}_{data.personal.surname}_{CV_TRANSLATION[lang]}.md"
            md_rendered.write_text(rendered)

            artifacts.setdefault("md", []).append(md_rendered)
            artifacts.setdefault(f"md_{lang}", []).append(md_rendered)

    return 0, artifacts


@task
def render_html(data_file: Path, job_title: str, langs: str, profiles: List[Set[str]]):
    artifacts = {}
    for lang in langs:
        for profile in profiles:
            data = get_data(data_file, lang, profile)

            env = Environment()
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


@task(depends=["compile_translations"])
def render_pdf(debug: bool, data_file: Path, job_title: str, langs: List[str], profiles: List[str]):
    artifacts = {}
    for lang in langs:
        tr = gettext.translation("messages", localedir="locales", languages=[lang])
        _ = tr.gettext
        for profile in profiles:
            data = get_data(data_file, lang, profile)

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

            if data.contacts.email:
                doc.append(_("Email: "))
                doc.append(Command("href", [f"mailto:{data.contacts.email}", f"{data.contacts.email}"]))
                doc.append(NewLine())

            if data.contacts.phone:
                doc.append(_("Phone: {phone}").format(phone=data.contacts.phone))
                doc.append(NewLine())

            if data.contacts.site:
                doc.append(f"Site: ")
                doc.append(Command("href", [f"{data.contacts.site}", f"{data.contacts.site}"]))
                doc.append(NewLine())

            if data.contacts.github:
                doc.append(f"Github: ")
                doc.append(Command("href", [f"https://github.com/{data.contacts.github}", f"{data.contacts.github}"]))
                doc.append(NewLine())

            with doc.create(Section(_("Work experience"), numbering=False)):
                for job in reversed(data.work_experience):
                    with doc.create(Subsection(_("{position} at {organization_name}").format(position=job.position, organization_name=job.organisation.name), numbering=False)):
                        doc.append(italic(_("{from_date} - Present").format(from_date=job.from_date) if job.current else _("{from_date} - {to_date}").format(from_date=job.from_date, to_date=job.to_date)))

                        bullets = Itemize()
                        for bullet in job.bullets:
                            bullets.add_item(f"{bullet}".strip("\n"))
                        doc.append(bullets)

                        if job.technologies:
                            doc.append(_("Key skills: "))
                            doc.append(italic(escape_latex(", ".join(job.technologies))))

            if data.education:
                with doc.create(Section(_("Education"), numbering=False)):
                    for education in reversed(data.education):
                        with doc.create(Subsection(f"{education.university} - {education.faculty}", numbering=False)):
                            doc.append(italic(f"{education.from_date} - {education.to_date}"))
                            doc.append(NewLine())
                            doc.append(f"{education.speciality}")

            out_dir = build_dir / "pdf"
            out_dir.mkdir(exist_ok=True, parents=True)
            cv_suffix = _("CV")
            out_file = out_dir / f"{data.personal.name}_{data.personal.surname}_{cv_suffix}.pdf"

            command = ["docker", "run", "-it", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{out_dir}:{out_dir}",
                       "-w", f"{out_dir}", "thomasweise/docker-texlive-full", "/usr/bin/pdflatex"]

            doc.generate_pdf(str(out_file)[:-4], clean=not debug, clean_tex=not debug, compiler=command[0], compiler_args=command[1:])

            artifacts.setdefault("pdf", []).append(out_file)
            artifacts.setdefault(f"pdf_{lang}", []).append(out_file)

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


@task
def compile_translations():
    run(["pybabel", "compile", "-d", "locales"], check=True)


@task
def update_translations():
    run(["pybabel", "extract", "-o", "locales/messages.pot", "dogefile.py"], check=True)
    run(["pybabel", "update", "-i", "locales/messages.pot", "-d", "locales"], check=True)

