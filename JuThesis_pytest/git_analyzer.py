import re
import subprocess
from pathlib import Path
from typing import Set, List

from JuThesis_pytest.scanner import FunctionScanner


class GitAnalyzer:
    def __init__(self, root: Path, function_scanner: FunctionScanner):
        self.root = root
        self.function_scanner = function_scanner
        self.git_root = self._get_git_root()
        self._verify_git_repo()

    def _get_git_root(self) -> Path:
        # Получение корня git-репозитория
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=self.root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
        return self.root

    def _verify_git_repo(self) -> None:
        # Проверка, что директория является git репозиторием
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=self.root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise ValueError(f"{self.root} is not a git repository")

    def get_modified_files(
            self,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> List[Path]:
        # Формирование команды для получения измененных файлов
        if target_ref:
            cmd = ["git", "diff", "--name-only", base_ref, target_ref]
        else:
            cmd = ["git", "diff", "--name-only", base_ref]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # Обработка ошибок выполнения git команды
            raise RuntimeError(f"Git command failed: {e.stderr}") from e

        files = []
        for line in result.stdout.strip().split("\n"):
            if line and line.endswith(".py"):
                # Git возвращает путь относительно git root
                file_path = (self.git_root / line).resolve()

                # Проверяем что файл внутри self.root (нашего скоупа анализа)
                try:
                    file_path.relative_to(self.root.resolve())
                    if file_path.exists():
                        files.append(file_path)
                except ValueError:
                    # Файл вне нашего скоупа анализа, пропускаем
                    continue

        return files

    def get_modified_lines(
            self,
            file_path: Path,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> Set[int]:
        # Путь относительно git root для команды git diff
        try:
            relative_path = file_path.relative_to(self.git_root)
        except ValueError:
            # Файл вне git репозитория
            return set()

        # Формирование команды для получения diff с контекстом 0
        if target_ref:
            cmd = ["git", "diff", "-U0", base_ref, target_ref, "--", str(relative_path)]
        else:
            cmd = ["git", "diff", "-U0", base_ref, "--", str(relative_path)]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.git_root,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError:
            return set()

        return self._parse_diff_lines(result.stdout)

    @staticmethod
    def _parse_diff_lines(diff_output: str) -> Set[int]:
        # Парсинг вывода git diff для извлечения номеров измененных строк
        # Формат: @@ -old_start,old_count +new_start,new_count @@
        modified_lines = set()
        pattern = re.compile(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')

        for match in pattern.finditer(diff_output):
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) else 1

            # Добавляем диапазон изменённых строк
            modified_lines.update(range(start, start + count))

        return modified_lines

    def get_modified_functions(
            self,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> Set[str]:
        # Получение списка измененных файлов
        modified_files = self.get_modified_files(base_ref, target_ref)
        if not modified_files:
            return set()

        # Построение индекса всех функций в проекте
        function_index = self.function_scanner.build_index()
        modified_functions = set()

        for file_path in modified_files:
            if file_path not in function_index:
                continue

            # Получение измененных строк в файле
            modified_lines = self.get_modified_lines(file_path, base_ref, target_ref)
            if not modified_lines:
                continue

            functions = function_index[file_path]

            # Проверка пересечения строк функций с изменёнными строками
            for func in functions:
                func_lines = set(range(func.start_line, func.end_line + 1))
                if func_lines & modified_lines:
                    modified_functions.add(func.identifier)

        return modified_functions
