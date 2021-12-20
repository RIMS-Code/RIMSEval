"""Configuration file for testing the package with ``nox``."""

import nox


nox.options.sessions = "lint", "safety", "tests"

package = "rimseval"
locations = "rimseval", "noxfile.py"
python_default = "3.9"
python_suite = ["3.9", "3.8", "3.7", "3.6"]


@nox.session(python=python_default)
def black(session):
    """Autoformat all python files with black."""
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


# @nox.session(python=python_default)
# def build(session):
#     """Pack rimstiming for release on PyPi."""
#     session.install("flit")
#     session.run("flit", "build")


@nox.session(python=python_default)
def docs(session):
    """Build the documentation."""
    session.install("sphinx", "sphinx_rtd_theme", "-r", "requirements.txt", "pytest")
    session.chdir("docs")
    session.run(
        "sphinx-build", "-b", "html", ".", "_build/html/"
    )  # as for readthedocs.io


@nox.session(python=python_default)
def lint(session):
    """Lint project using ``flake8``."""
    args = session.posargs or locations
    session.install("-r", "requirements-dev.txt")
    session.run("flake8", *args)


@nox.session(python=python_suite)
def tests(session):
    """Test the project using ``pytest``."""
    session.install("-r", "requirements.txt", "-r", "requirements-dev.txt")
    session.run("pytest")


@nox.session(python=python_default)
def safety(session):
    """Safety check for all dependencies."""
    session.install("safety", "-r", "requirements.txt", "-r", "requirements-dev.txt")
    session.run(
        "safety",
        "check",
        "--full-report",
    )


@nox.session(python=python_suite)
def xdoctest(session):
    """Test docstring examples with xdoctest."""
    args = session.posargs or ["all"]
    session.install("xdoctest[all]", "-r", "requirements.txt")
    session.run("python", "-m", "xdoctest", package, *args)
