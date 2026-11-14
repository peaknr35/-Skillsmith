import shutil
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf():
    return FIX / "sample.pdf"


@pytest.fixture
def scanned_pdf():
    return FIX / "scanned.pdf"


@pytest.fixture
def ws(tmp_path, sample_pdf):
    from skillsmith import workspace
    return workspace.scaffold(tmp_path / "run1", sample_pdf)
