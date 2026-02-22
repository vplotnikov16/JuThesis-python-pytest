import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

_durations = {}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    if call.when == "call":
        test_id = item.nodeid
        duration = call.duration
        _durations[test_id] = duration


def pytest_sessionfinish(session, exitstatus):
    output_file = Path.cwd() / ".test_durations.json"
    output_file.write_text(
        json.dumps(_durations, indent=2),
        encoding="utf-8"
    )
    print(f"\nTest durations saved to: {output_file}")
