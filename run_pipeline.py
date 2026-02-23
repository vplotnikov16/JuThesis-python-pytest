from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.scanner import FunctionScanner, FunctionInfo


def get_project_root() -> Path:
    # Возвращаем текущую директорию как корень проекта
    return Path.cwd()


def scan_functions() -> dict[Path, list[FunctionInfo]]:
    print("Scanning functions...")

    sample_root = get_project_root() / "sample_project"
    scanner = FunctionScanner(
        root=sample_root,
        include_patterns=["src/**/*.py"],
        exclude_patterns=["**/test_*.py", "**/__pycache__/**"]
    )
    return scanner.build_index()


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

    # Построение индекса функций
    function_index = scan_functions()
    # Вывод результатов
    total_functions = sum(len(funcs) for funcs in function_index.values())
    print(f"Found {total_functions} functions in {len(function_index)} files\n")

    # TODO: анализ изменений
    # TODO: сбор покрытия
    # TODO: сбор времени выполнения
    # TODO: построение протокола
    # TODO: сохранение input.json

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
