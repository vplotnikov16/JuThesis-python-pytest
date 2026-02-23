import json
from pathlib import Path
from typing import Dict


class DurationCollector:
    """ Сборщик времен выполнения тестов """

    def __init__(self, durations_file: Path):
        self.durations_file = durations_file

    def load(self) -> Dict[str, float]:
        """ Загружает времена выполнения из файла """
        if not self.durations_file.exists():
            return {}

        data = json.loads(self.durations_file.read_text(encoding="utf-8"))
        return {name: float(duration) for name, duration in data.items()}

    def get_test_time(self, test_id: str, default: float = 0.0) -> float:
        """ Геттер времени выполнения теста """
        durations = self.load()
        return durations.get(test_id, default)
