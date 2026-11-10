import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.core.rename_engine import execute_rename_plan
from src.core.sequence_insert import build_sequence_insert_plan
from src.core.file_scanner import scan_sequence
from src.gui.preview_dialog import show_rename_preview


class SequenceInsertFrame(ttk.Frame):
    def __init__(
        self, master, get_width, logger, initial_directory="",
        preview_geometry="", save_preview_geometry=None
    ):
        super().__init__(master, padding=10)
        self.get_width = get_width
        self.logger = logger
        self.preview_geometry = preview_geometry
        self.save_preview_geometry = save_preview_geometry

        self.directory_var = tk.StringVar(value=initial_directory)
        self.first_prefix_var = tk.StringVar(value="具名要求")
        self.second_prefix_var = tk.StringVar(value="具名要求xyz")
        self.tail_var = tk.StringVar(value="(n)")
        self.insert_after_var = tk.StringVar(value="3")
        self.output_prefix_var = tk.StringVar(value="指定文件名")
        self.start_var = tk.StringVar(value="1")

        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="目标目录：").pack(side="left")
        ttk.Entry(row, textvariable=self.directory_var).pack(
            side="left", fill="x", expand=True, padx=5
        )
        ttk.Button(row, text="选择目录", command=self._choose_directory).pack(side="left")

        ttk.Label(
            self,
            text="两组文件名均按“前缀 + 尾部格式（n 为数字）+ 扩展名”匹配；扩展名可不同且会保留。",
            wraplength=820
        ).pack(anchor="w", pady=(8, 10))

        for label, variable in (
            ("第一组前缀：", self.first_prefix_var),
            ("第二组前缀：", self.second_prefix_var),
        ):
            row = ttk.Frame(self)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=14).pack(side="left")
            ttk.Entry(row, textvariable=variable).pack(
                side="left", fill="x", expand=True, padx=5
            )

        row = ttk.Frame(self)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="共同尾部格式：", width=14).pack(side="left")
        ttk.Entry(row, textvariable=self.tail_var, width=14).pack(side="left", padx=5)
        ttk.Label(row, text="插入到第一组第 N 个文件之后（0 表示最前）：").pack(
            side="left", padx=(12, 4)
        )
        ttk.Entry(row, textvariable=self.insert_after_var, width=8).pack(side="left")

        row = ttk.Frame(self)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="起始序号：", width=14).pack(side="left")
        ttk.Entry(row, textvariable=self.start_var, width=10).pack(side="left", padx=5)

        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="合并后前缀：", width=14).pack(side="left")
        ttk.Entry(row, textvariable=self.output_prefix_var).pack(
            side="left", fill="x", expand=True, padx=5
        )

        ttk.Label(
            self,
            text="示例：插入位置为 3 时，结果顺序为第一组前 3 个、第二组全部、第一组剩余文件。",
            wraplength=820
        ).pack(anchor="w", pady=10)

        ttk.Button(self, text="预览并执行序列插入", command=self.process).pack(
            anchor="center", pady=12
        )

    def _choose_directory(self):
        directory = filedialog.askdirectory(parent=self)
        if directory:
            self.directory_var.set(directory)

    def _read_inputs(self):
        directory = self.directory_var.get().strip()
        first_prefix = self.first_prefix_var.get().strip()
        second_prefix = self.second_prefix_var.get().strip()
        tail = self.tail_var.get()
        output_prefix = self.output_prefix_var.get().strip()
        try:
            insert_after = int(self.insert_after_var.get())
            start = int(self.start_var.get())
        except ValueError as error:
            raise ValueError("插入位置和起始序号必须是整数") from error
        return directory, first_prefix, second_prefix, tail, insert_after, output_prefix, start

    @staticmethod
    def _signature(plan):
        return [(str(item.source), str(item.target)) for item in plan]

    def process(self):
        try:
            (directory, first_prefix, second_prefix, tail,
             insert_after, output_prefix, start) = self._read_inputs()

            first = scan_sequence(directory, first_prefix, tail)
            second = scan_sequence(directory, second_prefix, tail)
            total = len(first) + len(second)
            width = self.get_width(total)
            plan = build_sequence_insert_plan(
                directory, first_prefix, second_prefix, tail,
                insert_after, output_prefix, start, width
            )
            if not show_rename_preview(
                self, "确认序列插入", plan, self.preview_geometry,
                self._remember_preview_geometry
            ):
                return

            latest_first = scan_sequence(directory, first_prefix, tail)
            latest_second = scan_sequence(directory, second_prefix, tail)
            latest_total = len(latest_first) + len(latest_second)
            latest_width = self.get_width(latest_total)
            latest_plan = build_sequence_insert_plan(
                directory, first_prefix, second_prefix, tail,
                insert_after, output_prefix, start, latest_width
            )
            if self._signature(plan) != self._signature(latest_plan):
                messagebox.showwarning(
                    "目录内容已变化", "确认期间序列文件发生变化，请重新预览后再执行。",
                    parent=self
                )
                return

            execute_rename_plan(latest_plan, self.logger)
            messagebox.showinfo(
                "完成", f"已完成序列插入并重命名 {len(latest_plan)} 个文件。",
                parent=self
            )
        except Exception as error:
            self.logger.exception("文件序列插入失败")
            messagebox.showerror("序列插入失败", str(error), parent=self)

    def _remember_preview_geometry(self, geometry):
        self.preview_geometry = geometry
        if self.save_preview_geometry:
            self.save_preview_geometry(geometry)
