import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SequenceFile:
    name: str
    index: int
    extension: str


def filename_sort_key(filename: str):
    """按去掉最后一个扩展名后的文件名排序；扩展名用于稳定打破平局。"""
    stem, extension = os.path.splitext(filename)
    return stem, extension, filename


def list_files(directory: str, extension_filter: str = "*") -> list[str]:
    path = Path(directory)
    if not path.is_dir():
        raise NotADirectoryError(f"目录无效：{directory}")

    result = []
    for item in path.iterdir():
        if not item.is_file():
            continue
        if extension_filter != "*" and item.suffix.casefold() != extension_filter.casefold():
            continue
        result.append(item.name)
    return sorted(result, key=filename_sort_key)


def _sequence_regex(prefix: str, tail_format: str):
    if not prefix:
        raise ValueError("序列前缀不能为空")
    if tail_format.count("n") != 1:
        raise ValueError("尾部格式必须且仅包含一个小写字母 n")
    expression = re.escape(prefix) + re.escape(tail_format).replace("n", r"(?P<index>\d+)")
    return re.compile(expression)


def scan_sequence(directory: str, prefix: str, tail_format: str) -> list[SequenceFile]:
    """匹配一个序列；扩展名不参与匹配和数字排序，原样保留。"""
    path = Path(directory)
    if not path.is_dir():
        raise NotADirectoryError(f"目录无效：{directory}")

    matcher = _sequence_regex(prefix, tail_format)
    result = []
    for item in path.iterdir():
        if not item.is_file():
            continue
        stem, extension = os.path.splitext(item.name)
        match = matcher.fullmatch(stem)
        if match:
            result.append(SequenceFile(item.name, int(match.group("index")), extension))

    return sorted(result, key=lambda entry: (entry.index, entry.extension, entry.name))


def names_of(items: Iterable[SequenceFile]) -> list[str]:
    return [item.name for item in items]
