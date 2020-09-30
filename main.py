import sys
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy
from typing import List

from pylatex import Document, Section, Subsection
from pylatex.utils import italic

from jinja2 import Environment

from model import Data, load_data


class Runner:
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

        self._render_html(data)

        return 0

    def _render_latex(self, data: Data):
        doc = Document('basic')

        with doc.create(Section('A section')):
            doc.append('Some regular text and some ')
            doc.append(italic('italic text. '))

            with doc.create(Subsection('A subsection')):
                doc.append('Also some crazy characters: $&#{}')

        doc.generate_pdf('cv.pdf')

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
