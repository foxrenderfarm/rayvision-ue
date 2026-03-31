"""Test for analyze_ue_handle.py."""

# pylint: disable=import-error
import pytest

from rayvision_utils.exception.exception import CGFileNotExistsError


def test_check_path(ue_analyze):
    """Test init this interface.

    Test We can get an ``FileNameContainsChineseError`` if the information is
    wrong.

    """
    ue_analyze.cg_file = "xxx.uproject"
    with pytest.raises(CGFileNotExistsError):
        ue_analyze.check_path(ue_analyze.cg_file)
