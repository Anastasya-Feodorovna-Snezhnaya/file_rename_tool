import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from src.core.file_scanner import list_files
from src.core.rename_engine import RenameOperation, execute_rename_plan
from src.core.rename_rules import make_filename, validate_extension_filter, validate_name_parts
from src.gui.preview_dialog import show_rename_preview


class BatchRenameFrame(ttk.Frame):
    def __init__(
        self, master, get_width, logger, initial_directory="",
        preview_geometry="", save_preview_geometry=None
    ):
        super().__init__(master, padding=10)
        self.get_width = get_width
        self.logger = logger
        self.preview_geometry = preview_geometry
        self.save_preview_geometry = save_preview_geometry
        self.files = []

        self.directory_var = tk.StringVar(value=initial_directory)
        self.extension_var = tk.StringVar(value=".png")
        self.prefix_var = tk.StringVar(value="hello")
        self.tail_var = tk.StringVar(value="(n)")
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

        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="扩展名筛选：").pack(side="left")
        ttk.Entry(row, textvariable=self.extension_var, width=12).pack(side="left", padx=5)
        ttk.Label(row, text="输入 .png 等扩展名，或输入 * 表示全部格式").pack(side="left")

        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="新文件名前缀：").pack(side="left")
        ttk.Entry(row, textvariable=self.prefix_var).pack(
            side="left", fill="x", expand=True, padx=5
        )

        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="尾部格式：").pack(side="left")
        ttk.Entry(row, textvariable=self.tail_var, width=16).pack(side="left", padx=5)
        ttk.Label(row, text="起始序号：").pack(side="left", padx=(12, 0))
        ttk.Entry(row, textvariable=self.start_var, width=10).pack(side="left", padx=5)

        ttk.Label(self, text="文件列表（按去掉最后一个扩展名后的文件名排序，可鼠标拖选并复制）：").pack(
            anchor="w", pady=(8, 3)
        )
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)
        self.file_text = tk.Text(list_frame, wrap="none", state="disabled", height=12)
        vertical = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_text.yview)
        horizontal = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_text.xview)
        self.file_text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.file_text.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.file_text.bind("<Control-c>", self._copy_selection)
        self.file_text.bind("<Control-C>", self._copy_selection)

        row = ttk.Frame(self)
        row.pack(pady=10)
        ttk.Button(row, text="刷新文件列表", command=self.refresh).pack(side="left", padx=5)
        ttk.Button(row, text="开始处理", command=self.process).pack(side="left", padx=5)
        ttk.Button(row, text="清空列表", command=self.clear).pack(side="left", padx=5)

        if self.directory_var.get():
            self.refresh()

    def _copy_selection(self, event=None):
        try:
            selected = self.file_text.get("sel.first", "sel.last")
        except tk.TclError:
            return "break"
        self.clipboard_clear()
        self.clipboard_append(selected)
        return "break"

    def _choose_directory(self):
        directory = filedialog.askdirectory(parent=self)
        if directory:
            self.directory_var.set(directory)
            self.refresh()

    def _read_inputs(self):
        directory = self.directory_var.get().strip()
        extension = validate_extension_filter(self.extension_var.get())
        self.extension_var.set(extension)
        prefix = self.prefix_var.get().strip()
        tail = self.tail_var.get()
        validate_name_parts(prefix, tail)
        try:
            start = int(self.start_var.get())
        except ValueError as error:
            raise ValueError("起始序号必须是整数") from error
        return directory, extension, prefix, tail, start

    def refresh(self):
        try:
            directory = self.directory_var.get().strip()
            extension = validate_extension_filter(self.extension_var.get())
            self.extension_var.set(extension)
            self.files = list_files(directory, extension)
            self._update_list()
            self.logger.info("刷新文件列表：%s，共 %d 个文件", directory, len(self.files))
        except Exception as error:
            self.files = []
            self._update_list()
            self.logger.exception("刷新文件列表失败")
            messagebox.showerror("刷新失败", str(error), parent=self)

    def _update_list(self):
        self.file_text.configure(state="normal")
        self.file_text.delete("1.0", tk.END)
        if self.files:
            self.file_text.insert("1.0", "\n".join(self.files))
        self.file_text.configure(state="disabled")

    def _make_plan(self, files, directory, prefix, tail, start):
        width = self.get_width(len(files))
        root = Path(directory)
        return [
            RenameOperation(
                root / old_name,
                root / make_filename(prefix, tail, start + offset,
                                     Path(old_name).suffix, width)
            )
            for offset, old_name in enumerate(files)
        ]

    @staticmethod
    def _plan_signature(plan):
        return [(str(item.source), str(item.target)) for item in plan]

    def process(self):
        try:
            directory, extension, prefix, tail, start = self._read_inputs()
            files = list_files(directory, extension)
            if not files:
                messagebox.showwarning("没有文件", "当前筛选条件下没有可处理的文件。", parent=self)
                return
            plan = self._make_plan(files, directory, prefix, tail, start)
            if not show_rename_preview(
                self, "确认重命名", plan, self.preview_geometry,
                self._remember_preview_geometry
            ):
                return

            latest_files = list_files(directory, extension)
            latest_plan = self._make_plan(latest_files, directory, prefix, tail, start)
            if self._plan_signature(plan) != self._plan_signature(latest_plan):
                self.files = latest_files
                self._update_list()
                messagebox.showwarning(
                    "目录内容已变化", "确认期间目录文件发生变化。列表已更新，请重新检查预览后再执行。",
                    parent=self
                )
                return

            execute_rename_plan(latest_plan, self.logger)
            messagebox.showinfo("完成", f"已重命名 {len(latest_plan)} 个文件。", parent=self)
            self.refresh()
        except Exception as error:
            self.logger.exception("普通批量重命名失败")
            messagebox.showerror("重命名失败", str(error), parent=self)

    def _remember_preview_geometry(self, geometry):
        self.preview_geometry = geometry
        if self.save_preview_geometry:
            self.save_preview_geometry(geometry)

    def clear(self):
        self.files = []
        self.directory_var.set("")
        self._update_list()
