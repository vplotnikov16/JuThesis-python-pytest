from pathlib import Path
from typing import Dict, Set, List
from coverage import Coverage

from .scanner import FunctionScanner, FunctionInfo


class CoverageAnalyzer:
    """ Анализатор покрытия тестов """

    def __init__(self, coverage_file: Path, function_scanner: FunctionScanner):
        self.coverage_file = coverage_file
        self.function_scanner = function_scanner
        self._function_index = None

    @property
    def function_index(self) -> Dict[Path, List[FunctionInfo]]:
        """ Ленивая загрузка индекса функций """
        if self._function_index is None:
            self._function_index = self.function_scanner.build_index()
        return self._function_index

    def analyze(self) -> Dict[str, Set[str]]:
        """
        Проанализировать покрытие
        """
        cov = Coverage(data_file=str(self.coverage_file))
        cov.load()
        data = cov.get_data()

        test_to_functions: Dict[str, Set[str]] = {}

        for filename in data.measured_files():
            file_path = Path(filename)
            functions = self.function_index.get(file_path)
            if not functions:
                continue

            contexts_by_line = data.contexts_by_lineno(filename) or {}

            for line, contexts in contexts_by_line.items():
                func = self.function_scanner.find_function_at_line(functions, line)
                if not func:
                    continue

                for context in contexts:
                    # Контекст имеет формат "test_id|phase"
                    test_id, _, phase = context.partition("|")

                    # Игнорируем setup/teardown фазы
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
