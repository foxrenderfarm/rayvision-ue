"""The plugin of the pytest.

The pytest plugin hooks do not need to be imported into any test code, it will
load automatically when running pytest.

References:
    https://docs.pytest.org/en/2.7.3/plugins.html

"""

# pylint: disable=import-error
import pytest

from rayvision_ue.analyze_ue import AnalyzeUe


@pytest.fixture()
def analyze_info(tmpdir):
    """Get user info."""
    cg_file = str(tmpdir.join('test.uproject'))
    with open(cg_file, "w"):
        pass
    return {
        "cg_file": cg_file,
        "workspace": str(tmpdir),
        "software_version": "5.6.1",
        "project_name": "Project1",
        "plugin_config": {},
        "software_install_dir": "C:/Program Files/Epic Games/UE_5.6"
    }


@pytest.fixture()
def ue_analyze(analyze_info):
    """Create an UnrealEngine object."""
    return AnalyzeUe(**analyze_info)
