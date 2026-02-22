from typing import Dict, Set, List

from JuThesis.protocols.models import ProtocolInput, TestInfo


class ProtocolBuilder:
    def __init__(
            self,
            modified_functions: Set[str] | List[str],
            test_coverage: Dict[str, Set[str]],
            test_durations: Dict[str, float],
            time_budget: float,
            max_initial_coverage_size: int = 2
    ):
        self.modified_functions = list(modified_functions) if isinstance(modified_functions,
                                                                         set) else modified_functions
        self.test_coverage = test_coverage
        self.test_durations = test_durations
        self.time_budget = time_budget
        self.max_initial_coverage_size = max_initial_coverage_size

    def build(self) -> ProtocolInput:
        """ Построение ProtocolInput """
        # Оставляем только те тесты, которые покрывают modified_functions
        modified_set = set(self.modified_functions)
        available_tests = {}

        for test_id, covered_funcs in self.test_coverage.items():
            # Пересечение с modified_functions
            relevant_coverage = covered_funcs & modified_set

            if not relevant_coverage:
                # Тест не покрывает ни одной изменённой функции
                continue

            duration = self.test_durations.get(test_id, 0.0)
            if duration <= 0:
                # Пропускаем тесты с некорректным временем
                continue

            available_tests[test_id] = TestInfo(
                time=duration,
                covered_functions=sorted(relevant_coverage)
            )

        return ProtocolInput(
            version="1.0.0",
            modified_functions=sorted(self.modified_functions),
            available_tests=available_tests,
            time_budget=self.time_budget,
            max_initial_coverage_size=self.max_initial_coverage_size
        )
