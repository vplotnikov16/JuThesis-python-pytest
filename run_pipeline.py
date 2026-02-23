from pathlib import Path

from JuThesis_pytest import __version__


def get_project_root() -> Path:
    # Возвращаем текущую директорию как корень проекта
    return Path.cwd()


def main():
    print(f"JuThesis Python-Pytest Plugin v{__version__}")
    print("Starting pipeline...")

    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # TODO: инициализация компонентов
    # TODO: анализ изменений
    # TODO: сбор покрытия
    # TODO: сбор времени выполнения
    # TODO: построение протокола
    # TODO: сохранение input.json

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
