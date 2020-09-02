import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from pylatex import Document, Section, Subsection
from pylatex.utils import italic

from model import Data, load_data


class Runner:
    def __init__(self, args: List[str]):
        parser = ArgumentParser()
        parser.add_argument("--data-file", type=Path, default=Path("./data.yaml"))

        args = parser.parse_args(args)

        self.data_file = args.data_file

    def run(self) -> int:
        data = load_data(self.data_file)

        return 0

    def _render_latex(self, data: Data):
        doc = Document('basic')

        with doc.create(Section('A section')):
            doc.append('Some regular text and some ')
            doc.append(italic('italic text. '))

            with doc.create(Subsection('A subsection')):
                doc.append('Also some crazy characters: $&#{}')

        doc.generate_pdf('cv.pdf')


if __name__ == '__main__':
    runner = Runner(sys.argv[1:])
    exit_code = runner.run()
    exit(exit_code)
