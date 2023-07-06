import nox

SRC_FILES = [
    "bot",
    "noxfile.py",
]


def install_poetry_groups(session: nox.Session, *groups: str) -> None:
    session.run("poetry", "install", f"--with={','.join(groups)}")


@nox.session
def typecheck(session: nox.Session) -> None:
    install_poetry_groups(session, "typing")
    session.run("mypy", *SRC_FILES)


@nox.session
def lint(session: nox.Session) -> None:
    install_poetry_groups(session, "linting")
    session.run("black", "--check", *SRC_FILES)
    session.run("ruff", "check", *SRC_FILES)
    session.run("codespell", *SRC_FILES)


@nox.session
def fix(session: nox.Session) -> None:
    install_poetry_groups(session, "linting")
    session.run("black", *SRC_FILES)
    session.run("ruff", "check", "--fix", *SRC_FILES)
    session.run("codespell", "-w", "-i2", *SRC_FILES)
