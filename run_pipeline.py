from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.scanner import FunctionScanner, FunctionInfo
from JuThesis_pytest.git_analyzer import GitAnalyzer


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
    print(*map(lambda x: f' - {x}', modified_functions), sep="\n")

    # TODO: сбор покрытия
    # TODO: сбор времени выполнения
    # TODO: построение протокола
    # TODO: сохранение input.json

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
