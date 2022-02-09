"""Configuration file for testing the package with ``nox``."""

import nox


# todo: add lint and safety to mandatory tests
nox.options.sessions = ["tests"]

package = "rimseval"
locations = "rimseval", "noxfile.py"
python_default = "3.9"
python_suite = ["3.9", "3.8"]


@nox.session(python=python_default)
def docs(session):
    """Build the documentation."""
    session.install(".[doc]")
    session.chdir("docs")
    session.run(
        "sphinx-build", "-b", "html", ".", "_build/html/"
    )  # as for readthedocs.io


@nox.session(python=python_default)
def lint(session):
    """Lint project using ``flake8``."""
    args = session.posargs or locations
    session.install(".[dev]")
    session.run("flake8", *args)


@nox.session(python=python_suite)
def tests(session):
    """Test the project using ``pytest``."""
    session.install(".[test]")
    session.run("pytest")


@nox.session(python=python_default)
def safety(session):
    """Safety check for all dependencies."""
    session.install("safety", ".")
    session.run(
        "safety",
        "check",
        "--full-report",
    )
