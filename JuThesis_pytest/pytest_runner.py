import subprocess
from pathlib import Path


class PytestRunner:
    """ Запускает pytest программно для автоматического сбора данных """

    def __init__(self, project_root: Path, source_patterns: list[str]):
        self.project_root = project_root
        self.source_patterns = source_patterns

    def run_with_coverage_and_durations(self) -> bool:
        """
        Запускает pytest с coverage и сбором времени выполнения.

        :return: True если запуск успешен (даже если тесты упали)
        """
        # Формируем команду для pytest
        cmd = [
            "pytest",
            f"--cov={','.join(self.source_patterns)}",
            "--cov-context=test",
            "--cov-report=",  # Отключаем генерацию отчета
        ]

        print(f"Running: {' '.join(cmd)}")

        # Запуск pytest в директории проекта
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        # Проверяем результат
        # Код 0 = все тесты прошли, код 1 = есть упавшие тесты
        # Оба случая считаем успешными для наших целей
        if result.returncode in (0, 1):
            print("Pytest completed successfully")
            return True
        else:
            print(f"Pytest failed with code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return False
