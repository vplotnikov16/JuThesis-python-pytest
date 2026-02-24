from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.config import ConfigLoader
from JuThesis_pytest.orchestrator import PipelineOrchestrator


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

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

    # Создание оркестратора и запуск пайплайна
    orchestrator = PipelineOrchestrator(config)
    success = orchestrator.run_pipeline()

    # Возврат кода выхода
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
