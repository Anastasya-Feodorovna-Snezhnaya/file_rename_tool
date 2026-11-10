import re

INVALID_FILENAME_CHARS = set('\\\\/:*?"<>|')


def validate_name_parts(prefix: str, tail_format: str) -> None:
    if not prefix:
        raise ValueError("文件名前缀不能为空")
    if any(char in INVALID_FILENAME_CHARS for char in prefix):
        raise ValueError("文件名前缀包含 Windows 不允许的字符：\\ / : * ? \" < > |")
    if prefix.endswith((" ", ".")):
        raise ValueError("文件名前缀不能以空格或句点结尾")
    if tail_format.count("n") != 1:
        raise ValueError("尾部格式必须且仅包含一个小写字母 n")
    if any(char in INVALID_FILENAME_CHARS for char in tail_format):
        raise ValueError("尾部格式包含 Windows 不允许的字符：\\ / : * ? \" < > |")
    if tail_format.endswith((" ", ".")):
        raise ValueError("尾部格式不能以空格或句点结尾")


def validate_extension_filter(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("扩展名筛选条件不能为空；输入 * 表示全部格式")
    if value == "*":
        return value
    if not value.startswith("."):
        value = "." + value
    if any(char in value for char in "\\\\/:*?\"<>|"):
        raise ValueError("扩展名筛选条件包含非法字符")
    return value


def get_number_width(total_count: int, mode: str = "fixed",
                     extra_digits: int = 0, threshold_percent: int = 100) -> int:
    if total_count < 1:
        return 1
    base_width = len(str(total_count))
    if mode == "fixed":
        if not 0 <= extra_digits <= 5:
            raise ValueError("固定增加位数必须在 0～5 之间")
        return base_width + extra_digits
    if mode == "threshold":
        if not 0 <= threshold_percent <= 100:
            raise ValueError("容量阈值必须在 0～100 之间")
        capacity = 10 ** base_width
        ratio_percent = total_count / capacity * 100
        return base_width + (1 if ratio_percent > threshold_percent else 0)
    raise ValueError(f"未知编号位数模式：{mode}")


def format_index(index: int, width: int) -> str:
    return str(index).zfill(width)


def make_filename(prefix: str, tail_format: str, index: int,
                  extension: str, width: int) -> str:
    validate_name_parts(prefix, tail_format)
    number = format_index(index, width)
    return f"{prefix}{tail_format.replace('n', number)}{extension}"
