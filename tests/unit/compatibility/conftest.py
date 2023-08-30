"""PyTest fixtures for unit tests."""

from pathlib import Path

import pytest


@pytest.fixture
def legacy_files_path(request):
    """Provide the path to the `legacy_files` folder.

    :param request: PyTest request object

    :return: Path to the folder
    """
    curr = Path(request.fspath).parents[0]
    return Path(curr).joinpath("../legacy_files").absolute()
