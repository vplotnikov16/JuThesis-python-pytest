from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.scanner import FunctionScanner, FunctionInfo
from JuThesis_pytest.git_analyzer import GitAnalyzer
from JuThesis_pytest.coverage_analyzer import CoverageAnalyzer
from JuThesis_pytest.duration_collector import DurationCollector
from JuThesis_pytest.protocol_builder import ProtocolBuilder


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


def collect_durations() -> dict[str, float]:
    print("Collecting test durations...")

    sample_root = get_project_root() / "sample_project"
    durations_file = sample_root / ".test_durations.json"

    # Проверка наличия файла с длительностями
    if not durations_file.exists():
        print(f"Warning: Durations file not found at {durations_file}")
        print("Run: cd sample_project && pytest")
        return {}

    try:
        collector = DurationCollector(durations_file=durations_file)
        durations = collector.load()
        return durations

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return {}


def build_protocol(
    modified_functions: set[str],
    test_coverage: dict[str, set[str]],
    test_durations: dict[str, float]
):
    print("Building protocol...")

    # Параметры из конфигурации (пока заглушка)
    time_budget = 300.0  # 5 minut
    max_initial_coverage_size = 2

    try:
        builder = ProtocolBuilder(
            modified_functions=modified_functions,
            test_coverage=test_coverage,
            test_durations=test_durations,
            time_budget=time_budget,
            max_initial_coverage_size=max_initial_coverage_size
        )
        # Строим протокол
        protocol_input = builder.build()

        return protocol_input

    except ValueError as e:
        print(f"Error building protocol: {e}")
        return None


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

    # Сбор времени выполнения тестов
    test_durations = collect_durations()
    print(f"Found {len(test_durations)} test durations")

    # Построение протокола
    if modified_functions and test_coverage and test_durations:
        protocol_input = build_protocol(modified_functions, test_coverage, test_durations)
        if protocol_input:
            print("Protocol input created successfully")
    else:
        print("Skipping protocol building: missing required data")

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
