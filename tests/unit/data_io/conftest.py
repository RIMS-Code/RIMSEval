"""PyTest fixtures for unit tests in data_io."""

from pathlib import Path

import pytest


@pytest.fixture
def crd_data(request) -> Path:
    """Provide the path to the `crd_data` folder.

    This folder contains simple, small CRD files with real data for testing.

    :param request: PyTest request object.

    :return: Path to the folder
    """
    curr = Path(request.fspath).parents[0]
    return Path(curr).joinpath("../crd_data").absolute()


@pytest.fixture
def lst_crd_path(request):
    """Provide the path to the `lst_crd_files` folder.

    :param request: PyTest request object.

    :return: Path to the folder
    :rtype: Path
    """
    curr = Path(request.fspath).parents[0]
    return Path(curr).joinpath("lst_crd_files").absolute()
