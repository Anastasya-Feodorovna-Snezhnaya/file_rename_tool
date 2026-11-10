import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class NumberingSettings:
    mode: str = "fixed"
    extra_digits: int = 0
    threshold_percent: int = 100


class SettingsManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.path = Path.cwd() / "settings.json"
        self.settings = NumberingSettings()
        self.load()

    def load(self) -> NumberingSettings:
        if not self.path.exists():
            return self.settings
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            mode = data.get("mode", "fixed")
            extra = int(data.get("extra_digits", 0))
            threshold = int(data.get("threshold_percent", 100))
            if mode not in {"fixed", "threshold"}:
                raise ValueError("mode 必须为 fixed 或 threshold")
            if not 0 <= extra <= 5 or not 0 <= threshold <= 100:
                raise ValueError("编号位数设置超出允许范围")
            self.settings = NumberingSettings(mode, extra, threshold)
        except Exception:
            self.logger.exception("读取配置失败，使用默认设置：%s", self.path)
            self.settings = NumberingSettings()
        return self.settings

    def save(self) -> None:
        data = asdict(self.settings)
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8"
            )
            self.logger.info("配置已保存：%s", self.path)
        except Exception:
            self.logger.exception("保存配置失败：%s", self.path)
            raise
