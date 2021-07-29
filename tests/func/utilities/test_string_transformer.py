"""Test string transformations."""

from rimseval.utilities import string_transformer


def test_iso_to_iniabu_normal():
    """Transform 46Ti to Ti-46."""
    assert string_transformer.iso_to_iniabu("46Ti") == "Ti-46"
    assert string_transformer.iso_to_iniabu("235U") == "U-235"


def test_iso_to_iniabu_reversed():
    """Transform Ti46 to Ti-46."""
    assert string_transformer.iso_to_iniabu("Ti46") == "Ti-46"
    assert string_transformer.iso_to_iniabu("U235") == "U-235"
    assert string_transformer.iso_to_iniabu("Pt325") == "Pt-325"


def test_iso_to_iniabu_ignore_case():
    """Ignore case when transforming isotopes."""
    assert string_transformer.iso_to_iniabu("ti46") == "Ti-46"
    assert string_transformer.iso_to_iniabu("46tI") == "Ti-46"
