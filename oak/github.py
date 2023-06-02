from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy
from tempfile import TemporaryDirectory
from typing import List

from git import Repo
from github import Github, UnknownObjectException
from slugify import slugify


@dataclass
class GitUserInfo:
    name: str
    email: str


@dataclass
class GithubUserCredentials:
    user: str
    token: str


INFO_PAGE_REPO = "kirillsulim/kirillsulim"
CV_REPO = "kirillsulim/cv"


def commit_md_to_github(md_file: Path, git_user_info: GitUserInfo, robot_credentials: GithubUserCredentials):
    with TemporaryDirectory() as tmp_dir:
        repo = Repo.clone_from(
            f"https://{robot_credentials.user}:{robot_credentials.token}@github.com/{INFO_PAGE_REPO}", \
            tmp_dir,
            depth=1
        )
        repo_cv_file = Path(repo.working_tree_dir) / "cv.md"
        copy(md_file, repo_cv_file)

        repo.config_writer() \
            .set_value("user", "name", git_user_info.name) \
            .set_value("user", "email", git_user_info.email) \
            .release()

        repo.git.add(".")

        if repo.is_dirty():
            repo.git.commit("-m", "Automatic CV update")
            repo.git.push()


def release_pdf(pdf: List[Path], robot_credentials: GithubUserCredentials):
    if len(pdf) == 0:
        raise Exception("No artifacts to release")
    g = Github(robot_credentials.user, robot_credentials.token)
    cv_repo = g.get_repo(CV_REPO)

    build_time = datetime.now(timezone.utc)

    sha = Repo(".").head.commit.hexsha
    tag = build_time.strftime("%Y%m%d_%H%M%S")
    cv_repo.create_git_tag(tag, tag, sha, "commit")

    rel_name = datetime.now(timezone.utc).strftime("%Y %b %d %H:%M:%S %Z")
    rel_message = f"CV pdf built at {rel_name}"

    release = cv_repo.create_git_release(tag, rel_name, rel_message, draft=True)

    for pdf in pdf:
        path = str(pdf)
        name = slugify(pdf.stem) + "." + pdf.suffix
        label = str(pdf.name)
        release.upload_asset(path, name=name, label=label, content_type="application/pdf")

    release.update_release(release.title, release.body, draft=False)