import gettext

from pathlib import Path

from oak_build import run


TRANSLATION_DIR = Path("./oak/translation").resolve()
LOCALES_DIR = TRANSLATION_DIR / "locales"
BABEL_MAPPING = TRANSLATION_DIR / "babel-mapping.ini"
MESSAGES_POT = LOCALES_DIR / "messages.pot"


def compile_translations():
    run(f"pybabel compile -d {LOCALES_DIR}")


def update_translations():
    translation_sources = []
    translation_sources.append(Path("./oak_file.py"))
    translation_sources.extend(Path().glob("oak/**/*.py"))
    translation_sources.extend(Path().glob("oak/**/*.md"))
    translation_sources = [str(p) for p in translation_sources if p is not None]

    print(translation_sources)

    run(f"pybabel extract -F {BABEL_MAPPING} -o {MESSAGES_POT} {' '.join(translation_sources)}")
    run(f"pybabel update -i {MESSAGES_POT} -d {LOCALES_DIR}")


def get_translations(lang: str) -> gettext.GNUTranslations:
    return gettext.translation("messages", localedir=LOCALES_DIR, languages=[lang])
