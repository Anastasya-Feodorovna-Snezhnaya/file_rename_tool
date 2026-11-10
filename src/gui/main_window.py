import tkinter as tk
from tkinter import messagebox, ttk

from src.core.rename_rules import get_number_width
from src.gui.batch_rename import BatchRenameFrame
from src.gui.sequence_insert import SequenceInsertFrame
from src.utils.config import SettingsManager
from src.utils.logger import get_logger


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = get_logger()
        self.config_manager = SettingsManager(self.logger)
        self.settings = self.config_manager.settings

        root.title("批量文件重命名工具")
        root.geometry("900x700")
        root.minsize(760, 560)

        self._build_settings_panel()
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.batch_frame = BatchRenameFrame(
            notebook, get_width=self._get_width, logger=self.logger
        )
        self.sequence_frame = SequenceInsertFrame(
            notebook, get_width=self._get_width, logger=self.logger
        )
        notebook.add(self.batch_frame, text="普通批量重命名")
        notebook.add(self.sequence_frame, text="文件序列插入")

    def _build_settings_panel(self):
        frame = ttk.LabelFrame(self.root, text="编号位数设置")
        frame.pack(fill="x", padx=10, pady=8)

        self.mode_var = tk.StringVar(value=self.settings.mode)
        self.extra_var = tk.StringVar(value=str(self.settings.extra_digits))
        self.threshold_var = tk.StringVar(value=str(self.settings.threshold_percent))

        ttk.Label(frame, text="模式：").pack(side="left", padx=(8, 2), pady=6)
        mode = ttk.Combobox(
            frame, textvariable=self.mode_var, state="readonly", width=16,
            values=("fixed", "threshold")
        )
        mode.pack(side="left", padx=4)
        mode.bind("<<ComboboxSelected>>", self._save_settings)

        ttk.Label(frame, text="固定额外位数（0～5）：").pack(side="left", padx=(10, 2))
        extra = ttk.Spinbox(frame, from_=0, to=5, textvariable=self.extra_var, width=5)
        extra.pack(side="left", padx=4)
        extra.bind("<FocusOut>", self._save_settings)

        ttk.Label(frame, text="自动阈值（0～100%）：").pack(side="left", padx=(10, 2))
        threshold = ttk.Spinbox(
            frame, from_=0, to=100, textvariable=self.threshold_var, width=5
        )
        threshold.pack(side="left", padx=4)
        threshold.bind("<FocusOut>", self._save_settings)

        ttk.Button(frame, text="保存设置", command=self._save_settings).pack(
            side="left", padx=10
        )

    def _save_settings(self, event=None):
        try:
            mode = self.mode_var.get()
            extra = int(self.extra_var.get())
            threshold = int(self.threshold_var.get())
            if mode not in {"fixed", "threshold"}:
                raise ValueError("请选择有效的编号位数模式")
            if not 0 <= extra <= 5:
                raise ValueError("固定额外位数必须在 0～5 之间")
            if not 0 <= threshold <= 100:
                raise ValueError("自动阈值必须在 0～100 之间")
            self.settings.mode = mode
            self.settings.extra_digits = extra
            self.settings.threshold_percent = threshold
            self.config_manager.save()
        except (ValueError, OSError) as error:
            messagebox.showerror("设置无效", str(error), parent=self.root)

    def _get_width(self, total_count: int) -> int:
        return get_number_width(
            total_count,
            self.settings.mode,
            self.settings.extra_digits,
            self.settings.threshold_percent,
        )
