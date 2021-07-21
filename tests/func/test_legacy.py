"""Test legacy functions."""

from rimseval.compatibility import lion_eval


def test_extract_block():
    """Extract a block from some data."""
    top_char = "# start_at_top"
    bott_char = "# end_at_bottom"
    data = [
        "# something",
        top_char,
        "0",
        "1",
        "2",
        bott_char + " something else longer",
        "3",
        "4",
        "5",
    ]
    data_block_exp = ["0", "1", "2"]
    # bottom char set automatically
    assert lion_eval._extract_block(data, top_char=top_char) == data_block_exp
