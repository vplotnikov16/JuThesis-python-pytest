import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from JuThesis.io.writers.json_writer import JsonWriter
from JuThesis.protocols.models import ProtocolInput

from .config import PluginConfig
from .coverage_analyzer import CoverageAnalyzer
from .duration_collector import DurationCollector
from .git_analyzer import GitAnalyzer
from .protocol_builder import ProtocolBuilder
from .pytest_runner import PytestRunner
from .scanner import FunctionScanner, FunctionInfo


@dataclass
class CacheEntry:
    # Запись в кеше с метаданными
    data: Any
    files_hash: str
    config_hash: str


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
        
        # Настройки кеширования
        self._cache_enabled = config.cache_enabled
        self._cache_dir = config.cache_dir
        if self._cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_files_hash(self, file_patterns: list[str]) -> str:
        # Вычисляем hash всех файлов по паттернам
        files_data = []
        
        for pattern in file_patterns:
            for file_path in self.config.sample_project_root.glob(pattern):
                if file_path.is_file():
                    # Добавляем путь и время модификации
                    files_data.append({
                        'path': str(file_path.relative_to(self.config.sample_project_root)),
                        'mtime': file_path.stat().st_mtime
                    })
        
        # Сортируем для стабильности
        files_data.sort(key=lambda x: x['path'])
        
        serialized = json.dumps(files_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def _compute_config_hash(self) -> str:
        # Вычисляем hash параметров конфигурации
        config_data = {
            'source_patterns': self.config.source_patterns,
            'exclude_patterns': self.config.exclude_patterns,
            'base_ref': self.config.base_ref,
            'target_ref': self.config.target_ref,
        }
        serialized = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        # Получаем путь к файлу кеша
        return self._cache_dir / f"{cache_key}.pkl"

    def _is_cache_valid(self, cache_key: str, file_patterns: list[str]) -> bool:
        # Проверяем актуальность кеша
        if not self._cache_enabled:
            return False
        
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'rb') as f:
                entry: CacheEntry = pickle.load(f)
            
            # Проверяем hash файлов
            current_files_hash = self._compute_files_hash(file_patterns)
            if entry.files_hash != current_files_hash:
                return False
            
            # Проверяем hash конфигурации
            current_config_hash = self._compute_config_hash()
            if entry.config_hash != current_config_hash:
                return False
            
            return True
            
        except (pickle.PickleError, EOFError, AttributeError):
            return False

    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        # Загружаем данные из кеша
        if not self._cache_enabled:
            return None
        
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                entry: CacheEntry = pickle.load(f)
            return entry.data
        except (pickle.PickleError, EOFError, AttributeError):
            return None

    def _save_to_cache(self, cache_key: str, data: Any, file_patterns: list[str]) -> None:
        # Сохраняем данные в кеш
        if not self._cache_enabled:
            return
        
        cache_path = self._get_cache_path(cache_key)
        
        try:
            entry = CacheEntry(
                data=data,
                files_hash=self._compute_files_hash(file_patterns),
                config_hash=self._compute_config_hash()
            )
            
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
        except (pickle.PickleError, OSError):
            pass  # Тихо игнорируем ошибки кеширования

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

    def _build_function_index(self) -> dict[Path, list[FunctionInfo]]:
        # Построение индекса функций с кешированием
        cache_key = 'function_index'
        
        # Проверяем кеш
        if self._is_cache_valid(cache_key, self.config.source_patterns):
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                print("Loading function index from cache...")
                return cached
        
        # Строим индекс
        print("Building function index...")
        index = self._function_scanner.build_index()
        
        # Сохраняем в кеш
        self._save_to_cache(cache_key, index, self.config.source_patterns)
        
        return index

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
        # Сбор информации о покрытии тестов с кешированием
        cache_key = 'test_coverage'
        
        # Проверяем наличие файла coverage
        if not self._ensure_coverage_exists():
            print("Failed to generate coverage data")
            return {}
        
        # Проверяем кеш
        coverage_patterns = self.config.source_patterns + [str(self.config.coverage_file)]
        if self._is_cache_valid(cache_key, coverage_patterns):
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                print("Loading coverage from cache...")
                return cached
        
        # Собираем данные
        print("Collecting coverage...")
        try:
            test_coverage = self._coverage_analyzer.analyze()
            print(f"Found {len(test_coverage)} tests with coverage data")
            
            # Сохраняем в кеш
            self._save_to_cache(cache_key, test_coverage, coverage_patterns)
            
            return test_coverage
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return {}

    def _collect_durations(self) -> dict[str, float]:
        # Сбор времени выполнения тестов с кешированием
        cache_key = 'test_durations'
        
        # Проверяем наличие файла durations
        if not self._ensure_durations_exist():
            print("Failed to generate durations data")
            return {}
        
        # Проверяем кеш
        duration_patterns = [str(self.config.durations_file)]
        if self._is_cache_valid(cache_key, duration_patterns):
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                print("Loading durations from cache...")
                return cached
        
        # Собираем данные
        print("Collecting test durations...")
        try:
            test_durations = self._duration_collector.load()
            
            # Вывод статистики
            stats = self._duration_collector.get_statistics()
            print(f"Found {stats['total_tests']} test durations")
            if stats['total_tests'] > 0:
                print(f"Average duration: {stats['average_time']:.3f}s")
            
            # Сохраняем в кеш
            self._save_to_cache(cache_key, test_durations, duration_patterns)
            
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
        
        # Построение индекса функций с кешированием
        self._function_index = self._build_function_index()
        total_functions = sum(len(funcs) for funcs in self._function_index.values())
        print(f"Indexed {total_functions} functions in {len(self._function_index)} files")
        
        # Выполнение этапов сбора данных с кешированием
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
    
    def clear_cache(self) -> int:
        # Очистка всех файлов кеша
        if not self._cache_enabled or not self._cache_dir.exists():
            return 0
        
        count = 0
        for cache_file in self._cache_dir.glob('*.pkl'):
            cache_file.unlink()
            count += 1
        
        if count > 0:
            print(f"Cleared {count} cache files")
        
        return count
