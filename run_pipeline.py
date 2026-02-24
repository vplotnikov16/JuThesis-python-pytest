from pathlib import Path

from JuThesis_pytest import __version__
from JuThesis_pytest.config import ConfigLoader
from JuThesis_pytest.orchestrator import PipelineOrchestrator
from JuThesis_pytest.protocol_builder import ProtocolBuilder


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")

    # Загрузка конфигурации
    config_path = Path.cwd() / "config.yaml"
    print(f"Loading configuration from {config_path}...")
    try:
        config = ConfigLoader.load(config_path)
    except FileNotFoundError:
        print("Config file not found, creating default...")
        ConfigLoader.create_default_config(config_path)
        config = ConfigLoader.load(config_path)

    # Создание оркестратора
    orchestrator = PipelineOrchestrator(config)
    # Выполнение сбора данных
    modified_functions, test_coverage, test_durations = orchestrator.collect()
    # Построение протокола
    if modified_functions and test_coverage and test_durations:
        print("Building protocol input...")
        try:
            builder = ProtocolBuilder(
                modified_functions=modified_functions,
                test_coverage=test_coverage,
                test_durations=test_durations,
                time_budget=config.time_budget,
                max_initial_coverage_size=config.max_initial_coverage_size
            )
            protocol_input = builder.build()
            
            print("Protocol input created successfully")
            print(f"Output will be saved to: {config.input_json_path}")
            print()
            
        except ValueError as e:
            print(f"Error building protocol: {e}")
    else:
        print("Skipping protocol building: missing required data")
        print()

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
