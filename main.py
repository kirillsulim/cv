import sys
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy
from typing import List

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

from model import Data, get_data


class Runner:
    CV_TRANSLATION = {
        "en": "CV",
        "ru": "Резюме",
    }

    def __init__(self, args: List[str]):
        parser = ArgumentParser()
        parser.add_argument("--data-file", type=Path, default=Path("./data.yaml"))
        parser.add_argument("--lang", choices=["ru", "en"], default="ru")
        parser.add_argument("--profiles", nargs="+", default=set())
        parser.add_argument("--debug", action="store_true")

        args = parser.parse_args(args)

        self.data_file = args.data_file
        self.lang = args.lang
        self.profiles = args.profiles
        self.build_dir = Path("./build")
        self.debug = args.debug

    def run(self) -> int:
        data = get_data(self.data_file, self.lang, self.profiles)

        self._render_html(data)
        self._render_latex(data)
        # self._upload_to_gdrive()
        # self._upload_to_hh(data)
        self._render_md(data)

        return 0

    def _render_latex(self, data: Data):
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
        doc.append(LargeText("Java developer"))
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

        out_dir = self.build_dir / "pdf"
        out_dir.mkdir(exist_ok=True, parents=True)
        out_file = out_dir / f"{data.personal.name}_{data.personal.surname}_{self.CV_TRANSLATION[self.lang]}"
        doc.generate_pdf(str(out_file), clean=not self.debug, clean_tex=not self.debug)

    def _render_html(self, data: Data):
        env = Environment()
        template = env.from_string(Path("./resources/html/index.html").read_text())
        rendered = template.render(data=data, lang=self.lang, job_title="Java developer")

        html_dir = self.build_dir / "html"
        html_dir.mkdir(exist_ok=True, parents=True)
        copy(Path("./resources/html/style.css"), html_dir / "style.css")
        copy(Path("./resources/html/sulim.jpg"), html_dir / "sulim.jpg")

        html_rendered = html_dir / "index.html"
        html_rendered.write_text(rendered)

    def _render_md(self, data: Data):
        env = Environment()
        template = env.from_string(Path("./resources/md/template.md").read_text())
        rendered = template.render(data=data, lang=self.lang, job_title="Java developer")

        md_dir = self.build_dir / "md"
        md_dir.mkdir(exist_ok=True, parents=True)
        md_rendered = md_dir / f"{data.personal.name}_{data.personal.surname}_{self.CV_TRANSLATION[self.lang]}.md"
        md_rendered.write_text(rendered)

    def _upload_to_gdrive(self):
        pass

    def _upload_to_hh(self, data: Data):
        pass


if __name__ == '__main__':
    runner = Runner(sys.argv[1:])
    exit_code = runner.run()
    exit(exit_code)
