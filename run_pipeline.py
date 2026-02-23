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


def analyze_changes(scanner: FunctionScanner) -> list[Path]:
    print("Analyzing changes...")

    sample_root = get_project_root() / "sample_project"

    # Создаем анализатор изменений
    analyzer = GitAnalyzer(root=sample_root, function_scanner=scanner)

    # Получаем измененные файлы в HEAD коммите
    try:
        modified_files = analyzer.get_modified_files(base_ref="HEAD~1", target_ref="HEAD")
        print(f"Found {len(modified_files)} modified Python files:")
        for file in modified_files:
            rel_path = file.relative_to(sample_root)
            print(f"  - {rel_path}")
        return modified_files
    except RuntimeError as e:
        print(f"Warning: {e}")
        return []


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
    modified_files = analyze_changes(scanner)
    print("Modified files:")
    print(*map(lambda x: f' - {x}', modified_files), sep="\n")

    # TODO: определение изменённых функций
    # TODO: сбор покрытия
    # TODO: сбор времени выполнения
    # TODO: построение протокола
    # TODO: сохранение input.json

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
