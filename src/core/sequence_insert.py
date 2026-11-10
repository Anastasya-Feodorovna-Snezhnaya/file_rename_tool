from pathlib import Path

from src.core.file_scanner import scan_sequence
from src.core.rename_engine import RenameOperation
from src.core.rename_rules import make_filename, validate_name_parts


def build_sequence_insert_plan(directory: str, first_prefix: str,
                               second_prefix: str, tail_format: str,
                               insert_after: int, output_prefix: str,
                               start_index: int, width: int) -> list[RenameOperation]:
    validate_name_parts(first_prefix, tail_format)
    validate_name_parts(second_prefix, tail_format)
    validate_name_parts(output_prefix, tail_format)

    first = scan_sequence(directory, first_prefix, tail_format)
    second = scan_sequence(directory, second_prefix, tail_format)
    if not first:
        raise ValueError(f"没有找到第一组序列：前缀“{first_prefix}”")
    if not second:
        raise ValueError(f"没有找到第二组序列：前缀“{second_prefix}”")

    first_names = {item.name for item in first}
    second_names = {item.name for item in second}
    overlap = first_names & second_names
    if overlap:
        raise ValueError("两组序列匹配到了相同文件：" + "、".join(sorted(overlap)))

    if not 0 <= insert_after <= len(first):
        raise ValueError(f"插入位置必须在 0～{len(first)} 之间")

    merged = first[:insert_after] + second + first[insert_after:]
    directory_path = Path(directory)
    operations = []
    for offset, item in enumerate(merged):
        index = start_index + offset
        target_name = make_filename(
            output_prefix, tail_format, index, item.extension, width
        )
        operations.append(
            RenameOperation(directory_path / item.name, directory_path / target_name)
        )
    return operations
