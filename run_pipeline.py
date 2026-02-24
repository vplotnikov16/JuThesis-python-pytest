from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.config import ConfigLoader
from JuThesis_pytest.coverage_analyzer import CoverageAnalyzer
from JuThesis_pytest.duration_collector import DurationCollector
from JuThesis_pytest.git_analyzer import GitAnalyzer
from JuThesis_pytest.protocol_builder import ProtocolBuilder
from JuThesis_pytest.scanner import FunctionScanner, FunctionInfo


def load_config(config_path: Path):
    """ Загрузка конфигурации из файла """
    print(f"Loading configuration from {config_path}...")
    try:
        config = ConfigLoader.load(config_path)
        return config
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Creating default config.yaml...")
        ConfigLoader.create_default_config(config_path)
        return ConfigLoader.load(config_path)


def scan_functions(config, scanner: FunctionScanner) -> dict[Path, list[FunctionInfo]]:
    print("Scanning functions...")
    return scanner.build_index()


def analyze_changes(config, scanner: FunctionScanner) -> set[str]:
    print("Analyzing changes...")

    # Используем параметры из конфигурации
    analyzer = GitAnalyzer(root=config.sample_project_root, function_scanner=scanner)

    try:
        modified_functions = analyzer.get_modified_functions(
            base_ref=config.base_ref,
            target_ref=config.target_ref
        )
        return modified_functions
        
    except RuntimeError as e:
        print(f"Warning: {e}")
        return set()


def analyze_coverage(config, scanner: FunctionScanner) -> dict[str, set[str]]:
    print("Analyzing coverage...")

    coverage_file = config.coverage_file_path

    # Проверка наличия .coverage файла
    if not coverage_file.exists():
        print(f"Warning: Coverage file not found at {coverage_file}")
        print(f"Run: cd {config.sample_project_root.name} && pytest --cov=src --cov-context=test")
        return {}

    try:
        analyzer = CoverageAnalyzer(coverage_file=coverage_file, function_scanner=scanner)
        test_coverage = analyzer.analyze()
        return test_coverage

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return {}


def collect_durations(config) -> dict[str, float]:
    print("Collecting test durations...")

    durations_file = config.durations_file_path

    # Проверка наличия файла с длительностями
    if not durations_file.exists():
        print(f"Warning: Durations file not found at {durations_file}")
        print(f"Run: cd {config.sample_project_root.name} && pytest")
        return {}

    try:
        collector = DurationCollector(durations_file=durations_file)
        durations = collector.load()
        return durations

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return {}


def build_protocol(
    config,
    modified_functions: set[str],
    test_coverage: dict[str, set[str]],
    test_durations: dict[str, float]
):
    print("Building protocol...")

    # Используем параметры из конфигурации
    try:
        builder = ProtocolBuilder(
            modified_functions=modified_functions,
            test_coverage=test_coverage,
            test_durations=test_durations,
            time_budget=config.time_budget,
            max_initial_coverage_size=config.max_initial_coverage_size
        )
        protocol_input = builder.build()
        return protocol_input

    except ValueError as e:
        print(f"Error building protocol: {e}")
        return None


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

    # Загрузка конфигурации
    config_path = Path.cwd() / "config.yaml"
    config = load_config(config_path)
    
    # Вывод основных параметров конфигурации
    print(f"Project root: {config.project_root}")
    print(f"Sample project: {config.sample_project_root}")
    print(f"Time budget: {config.time_budget}s")

    # Создание сканера с параметрами из конфигурации
    scanner = FunctionScanner(
        root=config.sample_project_root,
        include_patterns=config.source_patterns,
        exclude_patterns=config.exclude_patterns
    )

    # Построение индекса функций
    function_index = scan_functions(config, scanner)
    total_functions = sum(len(funcs) for funcs in function_index.values())
    print(f"Found {total_functions} functions in {len(function_index)} files")

    # Анализ изменений
    modified_functions = analyze_changes(config, scanner)
    print("Modified functions:")
    if modified_functions:
        print(*map(lambda x: f' - {x}', modified_functions), sep="\n")
    else:
        print(" (none)")

    # Сбор покрытия
    test_coverage = analyze_coverage(config, scanner)
    print(f"Found {len(test_coverage)} tests")

    # Сбор времени выполнения тестов
    test_durations = collect_durations(config)
    print(f"Found {len(test_durations)} test durations")

    # Построение протокола
    if modified_functions and test_coverage and test_durations:
        protocol_input = build_protocol(
            config,
            modified_functions,
            test_coverage,
            test_durations
        )
        if protocol_input:
            print("Protocol input created successfully")
            print(f"Output will be saved to: {config.input_json_path}")
    else:
        print("Skipping protocol building: missing required data")

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
