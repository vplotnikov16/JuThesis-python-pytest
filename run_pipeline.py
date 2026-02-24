from pathlib import Path
import sys

from JuThesis_pytest import __version__
from JuThesis_pytest.config import ConfigLoader
from JuThesis_pytest.orchestrator import PipelineOrchestrator


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

    # Проверка аргументов командной строки
    args = sys.argv[1:]
    clear_cache = '--clear-cache' in args
    no_cache = '--no-cache' in args

    # Загрузка конфигурации
    config_path = Path.cwd() / "config.yaml"
    try:
        config = ConfigLoader.load(config_path)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        print("Creating default config...")
        ConfigLoader.create_default_config(config_path)
        config = ConfigLoader.load(config_path)
        print(f"Default config created at {config_path}")

    # Переопределение настройки кэша из аргументов
    if no_cache:
        config.cache_enabled = False
        print("Cache disabled")
        print()

    # Создание оркестратора
    orchestrator = PipelineOrchestrator(config)

    # Чистим кэш если нужно
    if clear_cache:
        print("Clearing cache...")
        count = orchestrator.clear_cache()
        if count > 0:
            print(f"Cache cleared ({count} files removed)")
        else:
            print("Cache is already empty")
        print()

    # Запуск пайплайна
    success = orchestrator.run_pipeline()

    # Возврат кода выхода
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
