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

from model import Data, load_data


class Runner:
    CV_TRANSLATION = {
        "en": "CV",
        "ru": "Резюме",
    }

    def __init__(self, args: List[str]):
        parser = ArgumentParser()
        parser.add_argument("--data-file", type=Path, default=Path("./data.yaml"))
        parser.add_argument("--lang", choices=["ru", "en"], default="ru")

        args = parser.parse_args(args)

        self.data_file = args.data_file
        self.lang = args.lang
        self.build_dir = Path("./build")

    def run(self) -> int:
        data = load_data(self.data_file)

        # self._render_html(data)
        self._render_latex(data)

        return 0

    def _render_latex(self, data: Data):
        lang = self.lang
        doc = Document(
            'basic',
            fontenc=["T2A", "T1"],
        )
        doc.packages.add(Package("babel", options=["main=russian", "english"]))
        doc.packages.add(Package("cmap"))
        doc.packages.add(Package("hyperref"))
        doc.packages.add(Package("erewhon"))

        doc.append(HugeText(bold(f"{data.personal.name[lang]} {data.personal.surname[lang]}")))
        doc.append(NewLine())
        doc.append(LargeText("Java developer"))
        doc.append(NewLine())
        doc.append(NewLine())

        doc.append(f"Email: ")
        doc.append(Command("href", [f"mailto:{data.personal.email}", f"{data.personal.email}"]))
        doc.append(NewLine())
        doc.append(f"Phone: {data.personal.phone}")
        doc.append(NewLine())
        doc.append(f"Site: ")
        doc.append(Command("href", [f"{data.personal.site}", f"{data.personal.site}"]))
        doc.append(NewLine())
        doc.append(f"Github: ")
        doc.append(Command("href", [f"https://github.com/{data.personal.github}", f"{data.personal.github}"]))
        doc.append(NewLine())

        with doc.create(Section('Work experience', numbering=False)):
            for job in reversed(data.work_experience):
                with doc.create(Subsection(f"{job.position[lang]} at {job.organisation.name[lang]}", numbering=False)):
                    doc.append(italic(f"{job.from_date} - {'Present' if job.current else job.to_date}"))

                    bullets = Itemize()
                    for bullet in job.bullets:
                        bullets.add_item(f"{bullet[lang]}".strip("\n"))
                    doc.append(bullets)

                    if job.technologies:
                        doc.append("Key skills: ")
                        doc.append(italic(escape_latex(", ".join(job.technologies))))

        with doc.create(Section("Education", numbering=False)):
            for education in reversed(data.education):
                with doc.create(Subsection(f"{education.university[lang]} - {education.faculty[lang]}", numbering=False)):
                    doc.append(italic(f"{education.from_date} - {education.to_date}"))
                    doc.append(NewLine())
                    doc.append(f"{education.speciality[lang]}")

        out_dir = self.build_dir / "pdf"
        out_dir.mkdir(exist_ok=True, parents=True)
        out_file = out_dir / f"{data.personal.name[lang]}_{data.personal.surname[lang]}_{self.CV_TRANSLATION[lang]}"
        doc.generate_pdf(str(out_file), clean=False, clean_tex=False)

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

        stop = True


if __name__ == '__main__':
    runner = Runner(sys.argv[1:])
    exit_code = runner.run()
    exit(exit_code)
