from typing import Optional

from JuThesis.io.writers.json_writer import JsonWriter
from JuThesis.protocols.models import ProtocolInput

from .config import PluginConfig
from .coverage_analyzer import CoverageAnalyzer
from .duration_collector import DurationCollector
from .git_analyzer import GitAnalyzer
from .protocol_builder import ProtocolBuilder
from .pytest_runner import PytestRunner
from .scanner import FunctionScanner


class PipelineOrchestrator:

    def __init__(self, config: PluginConfig):
        self.config = config
        
        # Компоненты инициализируются лениво
        self._function_scanner = None
        self._git_analyzer = None
        self._coverage_analyzer = None
        self._duration_collector = None
        self._pytest_runner = None
        
        # Кеш данных
        self._function_index = None
        self._modified_functions = None
        self._test_coverage = None
        self._test_durations = None

    def _initialize_components(self):
        # Инициализация всех компонентов пайплайна
        print("Initializing components...")
        
        self._function_scanner = FunctionScanner(
            root=self.config.sample_project_root,
            include_patterns=self.config.source_patterns,
            exclude_patterns=self.config.exclude_patterns
        )
        
        self._git_analyzer = GitAnalyzer(
            root=self.config.sample_project_root,
            function_scanner=self._function_scanner
        )
        
        self._coverage_analyzer = CoverageAnalyzer(
            coverage_file=self.config.coverage_file_path,
            function_scanner=self._function_scanner
        )
        
        self._duration_collector = DurationCollector(
            durations_file=self.config.durations_file_path
        )
        
        self._pytest_runner = PytestRunner(
            project_root=self.config.sample_project_root,
            source_patterns=self.config.source_patterns
        )

    def _detect_changes(self) -> set[str]:
        # Детектирование измененных функций через Git
        print("Detecting changes...")
        
        try:
            modified_functions = self._git_analyzer.get_modified_functions(
                base_ref=self.config.base_ref,
                target_ref=self.config.target_ref
            )
            
            print(f"Found {len(modified_functions)} modified functions")
            return modified_functions
            
        except RuntimeError as e:
            print(f"Warning: {e}")
            return set()

    def _ensure_coverage_exists(self) -> bool:
        # Проверка наличия coverage файла, при необходимости запуск pytest
        if self.config.coverage_file_path.exists():
            return True
        
        print("Coverage file not found, running pytest...")
        return self._pytest_runner.run_with_coverage_and_durations()

    def _ensure_durations_exist(self) -> bool:
        # Проверка наличия durations файла, при необходимости запуск pytest
        if self.config.durations_file_path.exists():
            return True
        
        print("Durations file not found, running pytest...")
        return self._pytest_runner.run_with_coverage_and_durations()

    def _collect_coverage(self) -> dict[str, set[str]]:
        # Сбор информации о покрытии тестов
        print("Collecting coverage...")
        
        if not self._ensure_coverage_exists():
            print("Failed to generate coverage data")
            return {}
        
        try:
            test_coverage = self._coverage_analyzer.analyze()
            print(f"Found {len(test_coverage)} tests with coverage data")
            return test_coverage
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return {}

    def _collect_durations(self) -> dict[str, float]:
        # Сбор времени выполнения тестов
        print("Collecting test durations...")
        
        if not self._ensure_durations_exist():
            print("Failed to generate durations data")
            return {}
        
        try:
            test_durations = self._duration_collector.load()
            
            # Вывод статистики
            stats = self._duration_collector.get_statistics()
            print(f"Found {stats['total_tests']} test durations")
            if stats['total_tests'] > 0:
                print(f"Average duration: {stats['average_time']:.3f}s")
            
            return test_durations
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return {}

    def _build_protocol_input(self) -> Optional[ProtocolInput]:
        # Построение ProtocolInput из собранных данных
        print("Building protocol input...")
        
        # Проверка наличия всех необходимых данных
        if not self._modified_functions:
            print("Warning: No modified functions found")
            return None
        
        if not self._test_coverage:
            print("Warning: No test coverage data available")
            return None
        
        if not self._test_durations:
            print("Warning: No test duration data available")
            return None
        
        try:
            builder = ProtocolBuilder(
                modified_functions=self._modified_functions,
                test_coverage=self._test_coverage,
                test_durations=self._test_durations,
                time_budget=self.config.time_budget,
                max_initial_coverage_size=self.config.max_initial_coverage_size
            )
            
            protocol_input = builder.build()
            
            # Вывод статистики
            print(f"Protocol input created:")
            print(f"  Modified functions: {len(protocol_input.modified_functions)}")
            print(f"  Available tests: {len(protocol_input.available_tests)}")
            print(f"  Time budget: {protocol_input.time_budget}s")
            
            return protocol_input
            
        except ValueError as e:
            print(f"Error building protocol: {e}")
            return None

    def _save_protocol_input(self, protocol_input: ProtocolInput) -> bool:
        # Сохранение ProtocolInput в JSON файл
        print("Saving protocol input...")
        
        try:
            # Создаем директорию вывода если нужно
            self.config.output_path.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем через JsonWriter из JuThesis
            JsonWriter.write(protocol_input, str(self.config.input_json_path))
            
            print(f"Protocol input saved to: {self.config.input_json_path}")
            return True
            
        except Exception as e:
            print(f"Error saving protocol input: {e}")
            return False

    def collect(self) -> tuple[set[str], dict[str, set[str]], dict[str, float]]:
        # Выполнить полный цикл сбора данных
        self._initialize_components()
        
        # Построение индекса функций
        print("Building function index...")
        self._function_index = self._function_scanner.build_index()
        total_functions = sum(len(funcs) for funcs in self._function_index.values())
        print(f"Indexed {total_functions} functions in {len(self._function_index)} files")
        
        # Выполнение этапов сбора данных
        self._modified_functions = self._detect_changes()
        self._test_coverage = self._collect_coverage()
        self._test_durations = self._collect_durations()
        
        return self._modified_functions, self._test_coverage, self._test_durations

    def run_pipeline(self) -> bool:
        # Полный пайплайн: сбор данных, построение протокола, сохранение
        self.collect()
        
        protocol_input = self._build_protocol_input()
        if protocol_input is None:
            print("Failed to build protocol input")
            return False
        
        success = self._save_protocol_input(protocol_input)
        return success
