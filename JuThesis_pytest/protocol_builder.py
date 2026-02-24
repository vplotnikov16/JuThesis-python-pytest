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
        # Валидация входных данных
        if not self.modified_functions:
            raise ValueError("No modified functions provided")
        
        if not self.test_coverage:
            raise ValueError("No test coverage data provided")
        
        if self.time_budget <= 0:
            raise ValueError(f"Time budget must be positive, got {self.time_budget}")

        # Оставляем только те тесты, которые покрывают modified_functions
        modified_set = set(self.modified_functions)
        available_tests = {}
        skipped_tests = 0
        missing_duration_tests = 0

        for test_id, covered_funcs in self.test_coverage.items():
            # Пересечение с modified_functions
            relevant_coverage = covered_funcs & modified_set

            if not relevant_coverage:
                skipped_tests += 1
                continue

            # Проверка наличия времени выполнения
            duration = self.test_durations.get(test_id)
            if duration is None:
                missing_duration_tests += 1
                continue
            
            if duration <= 0:
                # Такие тесты в расчет не идут
                continue

            available_tests[test_id] = TestInfo(
                time=duration,
                covered_functions=sorted(relevant_coverage)
            )

        # Проверка результата
        if not available_tests:
            raise ValueError(
                "No valid tests found. "
                f"Skipped {skipped_tests} tests without modified function coverage, "
                f"{missing_duration_tests} tests without duration data"
            )

        return ProtocolInput(
            version="1.0.0",
            modified_functions=sorted(self.modified_functions),
            available_tests=available_tests,
            time_budget=self.time_budget,
            max_initial_coverage_size=self.max_initial_coverage_size
        )

    def get_statistics(self) -> Dict[str, any]:
        # Статистика для отладки
        modified_set = set(self.modified_functions)
        
        # Подсчет тестов с релевантным покрытием
        relevant_tests = 0
        total_duration = 0.0
        
        for test_id, covered_funcs in self.test_coverage.items():
            relevant_coverage = covered_funcs & modified_set
            if relevant_coverage:
                relevant_tests += 1
                duration = self.test_durations.get(test_id, 0.0)
                if duration > 0:
                    total_duration += duration
        
        return {
            "modified_functions_count": len(self.modified_functions),
            "total_tests": len(self.test_coverage),
            "relevant_tests": relevant_tests,
            "tests_with_duration": len(self.test_durations),
            "total_duration": total_duration,
            "time_budget": self.time_budget,
            "budget_utilization": (total_duration / self.time_budget * 100) if self.time_budget > 0 else 0
        }
