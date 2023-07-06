import nox


def install_poetry_groups(session: nox.Session, *groups: str) -> None:
    session.run("poetry", "install", f"--with={','.join(groups)}")


@nox.session
def typecheck(session: nox.Session) -> None:
    install_poetry_groups(session, "typing")
    session.run("mypy", ".")


@nox.session
def lint(session: nox.Session) -> None:
    install_poetry_groups(session, "linting")
    session.run("black", "--check", ".")
    session.run("ruff", "check", ".")
    session.run("codespell", ".")


@nox.session
def fix(session: nox.Session) -> None:
    install_poetry_groups(session, "linting")
    session.run("black", ".")
    session.run("ruff", "check", "--fix", ".")
    session.run("codespell", "-w", "-i2", ".")
