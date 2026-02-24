from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.scanner import FunctionScanner, FunctionInfo
from JuThesis_pytest.git_analyzer import GitAnalyzer
from JuThesis_pytest.coverage_analyzer import CoverageAnalyzer


def get_project_root() -> Path:
    # Возвращаем текущую директорию как корень проекта
    return Path.cwd()


def scan_functions(scanner: FunctionScanner) -> dict[Path, list[FunctionInfo]]:
    print("Scanning functions...")
    return scanner.build_index()


def analyze_changes(scanner: FunctionScanner) -> set[str]:
    print("Analyzing changes...")

    sample_root = get_project_root() / "sample_project"

    # Создаем анализатор изменений
    analyzer = GitAnalyzer(root=sample_root, function_scanner=scanner)

    # Определяем измененные функции в HEAD коммите
    try:
        modified_functions = analyzer.get_modified_functions(
            base_ref="HEAD~1", target_ref="HEAD"
        )
        return modified_functions
        
    except RuntimeError as e:
        print(f"Warning: {e}")
        return set()


def analyze_coverage(scanner: FunctionScanner) -> dict[str, set[str]]:
    print("Analyzing coverage...")

    sample_root = get_project_root() / "sample_project"
    coverage_file = sample_root / ".coverage"

    # Проверка наличия .coverage файла
    if not coverage_file.exists():
        print(f"Warning: Coverage file not found at {coverage_file}")
        print("Run: cd sample_project && pytest --cov=src --cov-context=test")
        return {}

    try:
        # Создаем анализатор покрытия
        analyzer = CoverageAnalyzer(coverage_file=coverage_file, function_scanner=scanner)
        test_coverage = analyzer.analyze()
        return test_coverage

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return {}


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

    scanner = FunctionScanner(
        root=get_project_root() / "sample_project",
        include_patterns=["src/**/*.py"],
        exclude_patterns=["**/test_*.py", "**/__pycache__/**"]
    )

    # Построение индекса функций
    function_index = scan_functions(scanner)
    # Вывод результатов сканирования
    total_functions = sum(len(funcs) for funcs in function_index.values())
    print(f"Found {total_functions} functions in {len(function_index)} files")

    # Анализ изменений
    modified_functions = analyze_changes(scanner)
    print("Modified functions:")
    if modified_functions:
        print(*map(lambda x: f' - {x}', modified_functions), sep="\n")
    else:
        print(" (none)")

    # Сбор покрытия
    test_coverage = analyze_coverage(scanner)
    print(f"Found {len(test_coverage)} tests")

    # TODO: сбор времени выполнения
    # TODO: построение протокола
    # TODO: сохранение input.json

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
