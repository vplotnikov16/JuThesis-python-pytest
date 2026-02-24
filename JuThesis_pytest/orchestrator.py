from .config import PluginConfig
from .coverage_analyzer import CoverageAnalyzer
from .duration_collector import DurationCollector
from .git_analyzer import GitAnalyzer
from .scanner import FunctionScanner


class PipelineOrchestrator:
    """
    Координатор всех компонентов пайплайна.
    Управляет последовательным выполнением этапов сбора данных.
    """

    def __init__(self, config: PluginConfig):
        self.config = config
        
        # Компоненты инициализируются лениво
        self._function_scanner = None
        self._git_analyzer = None
        self._coverage_analyzer = None
        self._duration_collector = None
        
        # Кеш данных
        self._function_index = None
        self._modified_functions = None
        self._test_coverage = None
        self._test_durations = None

    def _initialize_components(self):
        """ Инициализация всех компонентов пайплайна """
        print("Initializing components...")
        
        # Создание сканера функций
        self._function_scanner = FunctionScanner(
            root=self.config.sample_project_root,
            include_patterns=self.config.source_patterns,
            exclude_patterns=self.config.exclude_patterns
        )
        
        # Создание анализатора изменений
        self._git_analyzer = GitAnalyzer(
            root=self.config.sample_project_root,
            function_scanner=self._function_scanner
        )
        
        # Создание анализатора покрытия
        self._coverage_analyzer = CoverageAnalyzer(
            coverage_file=self.config.coverage_file_path,
            function_scanner=self._function_scanner
        )
        
        # Создание сборщика длительностей
        self._duration_collector = DurationCollector(
            durations_file=self.config.durations_file_path
        )

    def _detect_changes(self) -> set[str]:
        """ Детектирование измененных функций через Git """
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

    def _collect_coverage(self) -> dict[str, set[str]]:
        """ Сбор информации о покрытии тестов """
        print("Collecting coverage...")
        
        # Проверка наличия файла покрытия
        if not self.config.coverage_file_path.exists():
            print(f"Warning: Coverage file not found at {self.config.coverage_file_path}")
            print(f"Run: cd {self.config.sample_project_root.name} && pytest --cov=src --cov-context=test")
            return {}
        
        try:
            test_coverage = self._coverage_analyzer.analyze()
            print(f"Found {len(test_coverage)} tests with coverage data")
            return test_coverage
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return {}

    def _collect_durations(self) -> dict[str, float]:
        """ Сбор времени выполнения тестов """
        print("Collecting test durations...")
        
        # Проверка наличия файла с длительностями
        if not self.config.durations_file_path.exists():
            print(f"Warning: Durations file not found at {self.config.durations_file_path}")
            print(f"Run: cd {self.config.sample_project_root.name} && pytest")
            return {}
        
        try:
            test_durations = self._duration_collector.load()
            
            # Вывод статистики
            stats = self._duration_collector.get_statistics()
            print(f"Found {stats['total_tests']} test durations")
            if stats['total_tests'] > 0:
                print(f"Average duration: {stats['average_duration']:.3f}s")
            
            return test_durations
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return {}

    def collect(self) -> tuple[set[str], dict[str, set[str]], dict[str, float]]:
        """
        Выполнить полный цикл сбора данных.
        
        :return: (modified_functions, test_coverage, test_durations)
        """
        # Инициализация компонентов
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
