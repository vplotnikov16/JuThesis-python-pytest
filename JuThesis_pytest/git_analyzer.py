"""Анализ изменений через git."""
import subprocess
from pathlib import Path
from typing import Set, List

from .scanner import FunctionScanner


class GitAnalyzer:
    """ Анализатор изменений через git """

    def __init__(self, root: Path, function_scanner: FunctionScanner):
        self.root = root
        self.function_scanner = function_scanner

    def get_modified_files(
            self,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> List[Path]:
        """ Получить список измененных файлов """
        if target_ref:
            cmd = ["git", "diff", "--name-only", base_ref, target_ref]
        else:
            cmd = ["git", "diff", "--name-only", base_ref]

        result = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True
        )

        files = []
        for line in result.stdout.strip().split("\n"):
            if line.endswith(".py"):
                files.append(self.root / line)

        return files

    def get_modified_lines(
            self,
            file_path: Path,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> Set[int]:
        """ Геттер номеров измененных строк в файле."""
        relative_path = file_path.relative_to(self.root)

        if target_ref:
            cmd = ["git", "diff", "-U0", base_ref, target_ref, "--", str(relative_path)]
        else:
            cmd = ["git", "diff", "-U0", base_ref, "--", str(relative_path)]

        result = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True
        )

        modified_lines = set()
        for line in result.stdout.split("\n"):
            if line.startswith("@@"):
                # Парсинг формата @@ -l,s +l,s @@
                parts = line.split()
                if len(parts) >= 3:
                    new_range = parts[2]  # +l,s
                    if new_range.startswith("+"):
                        range_str = new_range[1:]
                        if "," in range_str:
                            start, count = range_str.split(",")
                            start = int(start)
                            count = int(count)
                            modified_lines.update(range(start, start + count))
                        else:
                            modified_lines.add(int(range_str))

        return modified_lines

    def get_modified_functions(
            self,
            base_ref: str = "HEAD",
            target_ref: str | None = None
    ) -> Set[str]:
        """ Геттер идентификаторов измененных функций """
        modified_files = self.get_modified_files(base_ref, target_ref)
        function_index = self.function_scanner.build_index()

        modified_functions = set()

        for file_path in modified_files:
            if file_path not in function_index:
                continue

            modified_lines = self.get_modified_lines(file_path, base_ref, target_ref)
            functions = function_index[file_path]

            for func in functions:
                # Если хотя бы одна строка функции изменена
                func_lines = set(range(func.start_line, func.end_line + 1))
                if func_lines & modified_lines:
                    modified_functions.add(func.identifier)

        return modified_functions
