import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# Хранение времени выполнения тестов
_durations = {}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Сбор времени выполнения теста
    if call.when == "call":
        test_id = item.nodeid
        _durations[test_id] = call.duration


def pytest_sessionfinish(session, exitstatus):
    # Сохранение времени выполнения после завершения тестов
    output_dir = Path.cwd()
    
    durations_file = output_dir / ".test_durations.json"
    durations_file.write_text(
        json.dumps(_durations, indent=2),
        encoding="utf-8"
    )
