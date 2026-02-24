import ast
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Dict, Optional


@dataclass
class FunctionInfo:
    # Путь к модулю, где находится функция
    file: Path
    # Строка, в которой определяется функция
    line: int
    # Название функции
    name: str

    # Сохраняем информацию о том, какие строки занимает функция, чтобы отслеживать изменения
    # в git diff
    start_line: int
    end_line: int

    @property
    def identifier(self) -> str:
        # Уникальный идентификатор: file::line::name
        return f"{self.file}::{self.line}::{self.name}"


class FunctionScanner:
    def __init__(self, root: Path, include_patterns: List[str], exclude_patterns: List[str]):
        self.root = root
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

    def scan_files(self) -> Iterator[Path]:
        # Сканирование файлов по паттернам
        for pattern in self.include_patterns:
            for path in self.root.glob(pattern):
                if any(fnmatch.fnmatch(str(path), ex) for ex in self.exclude_patterns):
                    continue
                yield path

    @staticmethod
    def extract_functions(file_path: Path) -> List[FunctionInfo]:
        # Извлечение функций и методов из Python файла с помощью AST
        try:
            text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
            tree = ast.parse(text, filename=str(file_path))
        except SyntaxError:
            return []

        functions = []

        # Обход дерева AST для поиска функций и методов
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(FunctionInfo(
                    file=file_path,
                    line=node.lineno,
                    name=node.name,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                ))

        return functions

    def build_index(self) -> Dict[Path, List[FunctionInfo]]:
        # Построение индекса всех функций в проекте
        index = {}
        for file_path in self.scan_files():
            functions = self.extract_functions(file_path)
            if functions:
                index[file_path.resolve()] = functions
        return index

    @staticmethod
    def find_function_at_line(functions: List[FunctionInfo], line: int) -> Optional[FunctionInfo]:
        # Поиск функции по номеру строки
        for func in functions:
            if func.start_line <= line <= func.end_line:
                return func
        return None
