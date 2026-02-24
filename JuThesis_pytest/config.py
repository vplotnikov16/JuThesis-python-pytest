from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class PluginConfig:
    """ Конфигурация плагина JuThesis-python-pytest """

    # Пути проекта
    project_root: Path
    sample_project_root: Path

    # Паттерны сканирования
    source_patterns: List[str]
    test_patterns: List[str]
    exclude_patterns: List[str]

    # Git параметры
    base_ref: str
    target_ref: str

    # Пути к файлам данных
    coverage_file: Path
    durations_file: Path

    # Параметры JuThesis
    time_budget: float
    max_initial_coverage_size: int

    # Выходные файлы
    output_dir: Path
    input_json_name: str

    @property
    def coverage_file_path(self) -> Path:
        """ Полный путь к файлу coverage """
        return self.sample_project_root / self.coverage_file

    @property
    def durations_file_path(self) -> Path:
        """ Полный путь к файлу durations """
        return self.sample_project_root / self.durations_file

    @property
    def output_path(self) -> Path:
        """ Полный путь к директории вывода """
        return self.project_root / self.output_dir

    @property
    def input_json_path(self) -> Path:
        """ Полный путь к input.json """
        return self.output_path / self.input_json_name


class ConfigLoader:
    """
    Загрузчик конфигурации из YAML файла
    """

    @staticmethod
    def load(config_path: Path) -> PluginConfig:
        """ Загрузить конфигурацию из YAML файла """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Получаем корень проекта из конфига или используем директорию конфига
        project_root = Path(data.get('project', {}).get('root', config_path.parent))

        # Парсим секции конфигурации
        project_config = data.get('project', {})
        git_config = data.get('git', {})
        coverage_config = data.get('coverage', {})
        durations_config = data.get('durations', {})
        juthesis_config = data.get('juthesis', {})
        output_config = data.get('output', {})

        return PluginConfig(
            project_root=project_root,
            sample_project_root=project_root / project_config.get('sample_project', 'sample_project'),

            source_patterns=project_config.get('source_patterns', ['src/**/*.py']),
            test_patterns=project_config.get('test_patterns', ['tests/**/*.py']),
            exclude_patterns=project_config.get('exclude_patterns', [
                '**/test_*.py',
                '**/__pycache__/**',
                '**/migrations/**'
            ]),

            base_ref=git_config.get('base_ref', 'HEAD~1'),
            target_ref=git_config.get('target_ref', 'HEAD'),

            coverage_file=Path(coverage_config.get('file', '.coverage')),
            durations_file=Path(durations_config.get('file', '.test_durations.json')),

            time_budget=juthesis_config.get('time_budget', 300.0),
            max_initial_coverage_size=juthesis_config.get('max_initial_coverage_size', 2),

            output_dir=Path(output_config.get('directory', '.')),
            input_json_name=output_config.get('input_file', 'juthesis_input.json')
        )

    @staticmethod
    def create_default_config(output_path: Path) -> None:
        """ Создает файл конфигурации по умолчанию """
        default_config = {
            'project': {
                'root': '.',
                'sample_project': 'sample_project',
                'source_patterns': ['src/**/*.py'],
                'test_patterns': ['tests/**/*.py'],
                'exclude_patterns': [
                    '**/test_*.py',
                    '**/__pycache__/**',
                    '**/migrations/**'
                ]
            },
            'git': {
                'base_ref': 'HEAD~1',
                'target_ref': 'HEAD'
            },
            'coverage': {
                'file': '.coverage'
            },
            'durations': {
                'file': '.test_durations.json'
            },
            'juthesis': {
                'time_budget': 300.0,
                'max_initial_coverage_size': 2
            },
            'output': {
                'directory': '.',
                'input_file': 'juthesis_input.json'
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
