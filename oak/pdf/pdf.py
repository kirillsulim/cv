import os
from gettext import GNUTranslations
from pathlib import Path

from pylatex import Document, Section, Subsection, Package
from pylatex.base_classes import Command
from pylatex.basic import HugeText, NewLine, LargeText
from pylatex.utils import italic, bold, escape_latex
from pylatex.lists import Itemize

from oak.model import Data


def render_pdf(build_dir: Path, data: Data, job_title: str, translations: GNUTranslations, debug: bool = False) -> Path:
    _ = translations.gettext

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

    if data.contacts.telegram:
        doc.append(f"Telegram: ")
        doc.append(Command("href", [f"https://t.me/{data.contacts.telegram}", f"{data.contacts.telegram}"]))
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
    job_title = job_title.replace(" ", "_")
    out_file = out_dir / f"{data.personal.name}_{data.personal.surname}_{job_title}_{cv_suffix}.pdf"

    command = ["docker", "run", "-i", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{out_dir}:{out_dir}",
               "-w", f"{out_dir}", "thomasweise/docker-texlive-full", "/usr/bin/pdflatex"]

    doc.generate_pdf(str(out_file)[:-4], clean=not debug, clean_tex=not debug, compiler=command[0], compiler_args=command[1:])

    return out_file