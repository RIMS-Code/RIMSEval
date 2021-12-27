"""PyTest fixtures for unit tests."""

from pathlib import Path
import pytest


@pytest.fixture
def legacy_files_path(request):
    """Provides the path to the `legacy_files` folder.

    :return: Path to the folder
    :rtype: Path
    """
    curr = Path(request.fspath).parents[0]
    return Path(curr).joinpath("../legacy_files").absolute()
