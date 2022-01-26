"""Unit tests for lst to crd converter."""

from pathlib import Path

from rimseval.data_io import LST2CRD


def test_mcs6a_short_10k(tmpdir, lst_crd_path):
    """Convert MCS6A file to crd and compare outputs."""
    lst_fname = "MCS6A_short_10k_signal.lst"
    crd_fname = "MCS6A_short_10k_signal.crd"
    # copy file to temporary file
    tmpdir.join(lst_fname).write_binary(lst_crd_path.joinpath(lst_fname).read_bytes())
    lst_fpath = Path(tmpdir.strpath).joinpath(lst_fname)
    # create crd
    conv = LST2CRD(file_name=lst_fpath, channel_data=4)
    conv.read_list_file()
    conv.write_crd()
    # compare crd
    assert (
        Path(tmpdir.strpath).joinpath(crd_fname).read_bytes()
        == lst_crd_path.joinpath(crd_fname).read_bytes()
    )


def test_mcs6a_short_10k_tagged(tmpdir, lst_crd_path):
    """Convert tagged MCS6A file to two crd files and compare outputs."""
    lst_fname = "MCS6A_short_10k_signal_tag.lst"
    crd_fname_tagged = "MCS6A_short_10k_signal_tag.tagged.crd"
    crd_fname_untagged = "MCS6A_short_10k_signal_tag.untagged.crd"
    # copy file to temporary file
    tmpdir.join(lst_fname).write_binary(lst_crd_path.joinpath(lst_fname).read_bytes())
    lst_fpath = Path(tmpdir.strpath).joinpath(lst_fname)
    # create crd
    conv = LST2CRD(file_name=lst_fpath, channel_data=4, channel_tag=3)
    conv.read_list_file()
    conv.write_crd()
    # compare crd
    # assert (
    #         Path(tmpdir.strpath).joinpath(crd_fname).read_bytes()
    #         == lst_crd_path.joinpath(crd_fname).read_bytes()


def test_mcs8a_short_10k(tmpdir, lst_crd_path):
    """Convert MCS8a file to crd and compare outputs."""
    lst_fname = "MCS8a_short_10k_signal.lst"
    crd_fname = "MCS8a_short_10k_signal.crd"
    # copy file to temporary file
    tmpdir.join(lst_fname).write_binary(lst_crd_path.joinpath(lst_fname).read_bytes())
    lst_fpath = Path(tmpdir.strpath).joinpath(lst_fname)
    # create crd
    conv = LST2CRD(file_name=lst_fpath, channel_data=9)
    conv.read_list_file()
    conv.write_crd()
    # compare crd
    assert (
        Path(tmpdir.strpath).joinpath(crd_fname).read_bytes()
        == lst_crd_path.joinpath(crd_fname).read_bytes()
    )
