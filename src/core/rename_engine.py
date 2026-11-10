import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RenameOperation:
    source: Path
    target: Path


class RenameExecutionError(RuntimeError):
    pass


def _path_key(path: Path) -> str:
    # 使用大小写不敏感键预检，兼容 Windows 文件系统的常见行为。
    return os.path.normcase(os.path.abspath(str(path))).casefold()


def _preflight(operations: list[RenameOperation]) -> None:
    source_keys = [_path_key(item.source) for item in operations]
    target_keys = [_path_key(item.target) for item in operations]

    if len(set(source_keys)) != len(source_keys):
        raise ValueError("重命名计划包含重复的源文件")
    if len(set(target_keys)) != len(target_keys):
        raise ValueError("生成了重复的目标文件名，请调整前缀、尾部格式或编号")

    source_key_set = set(source_keys)
    for operation in operations:
        if not operation.source.is_file():
            raise FileNotFoundError(f"源文件不存在或不是普通文件：{operation.source}")
        if operation.source.parent != operation.target.parent:
            raise ValueError("当前重命名计划不允许跨目录移动文件")
        if operation.target.exists() and _path_key(operation.target) not in source_key_set:
            raise FileExistsError(f"目标文件已存在且不属于本次重命名集合：{operation.target}")


def _make_temp_path(source: Path) -> Path:
    while True:
        candidate = source.with_name(f".{source.name}.rename-{uuid.uuid4().hex}.tmp")
        if not candidate.exists():
            return candidate


def execute_rename_plan(operations: Iterable[RenameOperation],
                        logger: logging.Logger | None = None) -> None:
    operations = list(operations)
    if not operations:
        raise ValueError("没有可执行的重命名操作")

    _preflight(operations)
    staged: list[tuple[RenameOperation, Path]] = []
    completed: list[tuple[RenameOperation, Path]] = []

    try:
        # 第一阶段：所有源文件先改为同目录下的唯一临时名称。
        for operation in operations:
            temp_path = _make_temp_path(operation.source)
            os.rename(operation.source, temp_path)
            staged.append((operation, temp_path))

        # 第二阶段：临时名称改为最终名称。
        for operation, temp_path in staged:
            os.rename(temp_path, operation.target)
            completed.append((operation, temp_path))

    except Exception as original_error:
        rollback_errors = []

        # 先把已生成的最终文件移回临时名称，释放原始名称空间。
        for operation, temp_path in reversed(completed):
            try:
                if operation.target.exists():
                    os.rename(operation.target, temp_path)
            except Exception as rollback_error:
                rollback_errors.append(
                    f"{operation.target} -> {temp_path}: {rollback_error}"
                )

        # 再将仍存在的临时文件恢复为原始名称。
        for operation, temp_path in reversed(staged):
            try:
                if temp_path.exists():
                    os.rename(temp_path, operation.source)
            except Exception as rollback_error:
                rollback_errors.append(
                    f"{temp_path} -> {operation.source}: {rollback_error}"
                )

        # 不仅依赖异常列表，也检查每个原始路径是否实际恢复。
        for operation in operations:
            if not operation.source.exists():
                rollback_errors.append(f"原始文件未能恢复：{operation.source}")

        detail = f"重命名失败：{original_error}"
        if rollback_errors:
            detail += "\n回滚未能完全完成：\n" + "\n".join(rollback_errors)
        else:
            detail += "\n已尝试回滚，所有原始文件路径均已恢复。"
        if logger:
            logger.exception("执行重命名计划失败；%s", detail)
        raise RenameExecutionError(detail) from original_error

    if logger:
        logger.info("重命名完成，共处理 %d 个文件", len(operations))
