import oak.model as yaml_model
import oak.jsonresume.model as json_model


def _extract_basics(source: yaml_model.Data, job_title: str) -> json_model.Basics:
    profiles = []

    if source.contacts.telegram:
        profiles.append(json_model.Profile(
            network="Telegram",
            url=f"https://t.me/{source.contacts.telegram}",
            username=source.contacts.telegram
        ))

    if source.contacts.github:
        profiles.append(json_model.Profile(
            network="GitHub",
            url=f"https://github.com/{source.contacts.github}",
            username=source.contacts.github
        ))

    return json_model.Basics(
        name=f"{source.personal.name} {source.personal.surname}",
        label=job_title,
        image=None,
        phone=source.contacts.phone,
        url=source.contacts.site,
        summary=None,
        location=None,
        profiles=profiles,
    )


def _convert_education(source: yaml_model.Education) -> json_model.Education:
    return json_model.Education(
        institution=source.university,
        url=None,
        area=source.faculty,
        studyType=source.speciality,
        startDate=source.from_date,
        endDate=source.to_date,
        score=None,
        courses=[],
    )


def _convert_work(source: yaml_model.WorkExperience) -> json_model.Work:
    return json_model.Work(
        name=source.organisation.name,
        position=source.position,
        url=None,
        startDate=source.from_date,
        endDate=source.to_date,
        summary=None,
        highlights=source.bullets,
    )


def convert(source: yaml_model.Data, job_title: str):
    return json_model.JsonResume(
        basics=_extract_basics(source, job_title),
        work=list(reversed(list(map(_convert_work, source.work_experience)))),
        education=list(reversed(list(map(_convert_education, source.education)))),
    )
