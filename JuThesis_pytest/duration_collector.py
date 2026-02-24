import json
from pathlib import Path
from typing import Dict


class DurationCollector:

    def __init__(self, durations_file: Path):
        self.durations_file = durations_file

    def load(self) -> Dict[str, float]:
        # Загрузка времени выполнения тестов из JSON файла
        if not self.durations_file.exists():
            return {}

        try:
            data = json.loads(self.durations_file.read_text(encoding="utf-8"))
            return {name: float(duration) for name, duration in data.items()}
        except (json.JSONDecodeError, ValueError):
            return {}

    def get_test_time(self, test_id: str, default: float = 0.0) -> float:
        # Получение времени выполнения конкретного теста
        durations = self.load()
        return durations.get(test_id, default)

    def get_statistics(self) -> Dict:
        # Статистика по времени выполнения всех тестов
        durations = self.load()
        
        if not durations:
            return {
                'total_tests': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0
            }
        
        times = list(durations.values())
        return {
            'total_tests': len(durations),
            'total_time': sum(times),
            'average_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
