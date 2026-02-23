from pathlib import Path
from typing import Dict, Set, List, Optional
from coverage import Coverage

from .scanner import FunctionScanner, FunctionInfo


class CoverageAnalyzer:
    """ Анализатор покрытия тестов """

    def __init__(self, coverage_file: Path, function_scanner: FunctionScanner):
        self.coverage_file = coverage_file
        self.function_scanner = function_scanner
        self._function_index: Optional[Dict[Path, List[FunctionInfo]]] = None
        self._coverage_data = None

    @property
    def function_index(self) -> Dict[Path, List[FunctionInfo]]:
        """ Ленивая загрузка индекса функций """
        if self._function_index is None:
            self._function_index = self.function_scanner.build_index()
        return self._function_index

    @property
    def coverage_data(self):
        """ Ленивая загрузка coverage данных """
        if self._coverage_data is None:
            if not self.coverage_file.exists():
                raise FileNotFoundError(
                    f"Coverage file not found: {self.coverage_file}\n"
                    f"Run pytest with: pytest --cov=src --cov-context=test"
                )

            cov = Coverage(data_file=str(self.coverage_file))
            cov.load()
            self._coverage_data = cov.get_data()

            # Проверка наличия контекстов
            if not self._has_contexts():
                raise ValueError(
                    "Coverage file does not contain contexts.\n"
                    "Make sure pytest was run with --cov-context=test"
                )

        return self._coverage_data

    def _has_contexts(self) -> bool:
        # Проверка, есть ли контексты в coverage данных
        for filename in self._coverage_data.measured_files():
            contexts = self._coverage_data.contexts_by_lineno(filename)
            if contexts:
                return True
        return False

    def analyze(self) -> Dict[str, Set[str]]:
        """
        Проанализировать покрытие
        """
        # Анализ покрытия: возвращает mapping test_id -> covered_functions
        test_to_functions: Dict[str, Set[str]] = {}

        for filename in self.coverage_data.measured_files():
            file_path = Path(filename).resolve()

            if not file_path.suffix == '.py':
                continue

            functions = self.function_index.get(file_path)
            if not functions:
                continue

            contexts_by_line = self.coverage_data.contexts_by_lineno(filename)
            if not contexts_by_line:
                continue

            for line, contexts in contexts_by_line.items():
                func = self.function_scanner.find_function_at_line(functions, line)
                if not func:
                    continue

                for context in contexts:
                    # Парсинг контекста "test_id|phase"
                    test_id, _, phase = context.partition("|")

                    # Игнорируем setup/teardown фазы, оставляем только run
                    if phase not in ("", "run"):
                        continue

                    if not test_id:
                        continue

                    test_to_functions.setdefault(test_id, set()).add(
                        func.identifier
                    )

        return test_to_functions

    def get_all_functions(self) -> Set[str]:
        """ Геттер множества всех функций """
        all_functions = set()
        for functions in self.function_index.values():
            for func in functions:
                all_functions.add(func.identifier)
        return all_functions

    @staticmethod
    def get_covered_functions(
            test_coverage: Dict[str, Set[str]]
    ) -> Set[str]:
        """ Геттер множества покрытых функций """
        covered = set()
        for functions in test_coverage.values():
            covered.update(functions)
        return covered

    def get_uncovered_functions(
            self,
            test_coverage: Dict[str, Set[str]]
    ) -> Set[str]:
        """ Геттер множества непокрытых функций """
        all_funcs = self.get_all_functions()
        covered = self.get_covered_functions(test_coverage)
        return all_funcs - covered

    def get_coverage_statistics(self, test_coverage: Dict[str, Set[str]]) -> Dict:
        """ Статистика покрытия для отладки """
        all_functions = self.get_all_functions()
        covered_functions = self.get_covered_functions(test_coverage)

        return {
            'total_tests': len(test_coverage),
            'total_functions': len(all_functions),
            'covered_functions': len(covered_functions),
            'uncovered_functions': len(all_functions - covered_functions),
            'coverage_percentage': len(covered_functions) / len(all_functions) * 100 if all_functions else 0,
        }
