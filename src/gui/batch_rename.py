import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from src.core.file_scanner import list_files
from src.core.rename_engine import RenameOperation, execute_rename_plan
from src.core.rename_rules import make_filename, validate_extension_filter, validate_name_parts


class BatchRenameFrame(ttk.Frame):
    def __init__(self, master, get_width, logger):
        super().__init__(master, padding=10)
        self.get_width = get_width
        self.logger = logger
        self.files = []

        self.directory_var = tk.StringVar()
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
        ttk.Entry(row, textvariable=self.prefix_var, width=20).pack(side="left", padx=5)
        ttk.Label(row, text="尾部格式：").pack(side="left")
        ttk.Entry(row, textvariable=self.tail_var, width=12).pack(side="left", padx=5)
        ttk.Label(row, text="起始序号：").pack(side="left")
        ttk.Entry(row, textvariable=self.start_var, width=8).pack(side="left", padx=5)

        ttk.Label(self, text="文件列表（按去掉最后一个扩展名后的文件名排序）：").pack(
            anchor="w", pady=(8, 3)
        )
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)
        self.file_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = ttk.Frame(self)
        row.pack(pady=10)
        ttk.Button(row, text="刷新文件列表", command=self.refresh).pack(side="left", padx=5)
        ttk.Button(row, text="开始处理", command=self.process).pack(side="left", padx=5)
        ttk.Button(row, text="清空列表", command=self.clear).pack(side="left", padx=5)

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
            directory, extension, _, _, _ = self._read_inputs()
            self.files = list_files(directory, extension)
            self._update_list()
            self.logger.info("刷新文件列表：%s，共 %d 个文件", directory, len(self.files))
        except Exception as error:
            messagebox.showerror("刷新失败", str(error), parent=self)

    def _update_list(self):
        self.file_listbox.delete(0, tk.END)
        for name in self.files:
            self.file_listbox.insert(tk.END, name)

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
            # 执行前重新扫描，不信任上次刷新时缓存的文件列表。
            files = list_files(directory, extension)
            if not files:
                messagebox.showwarning("没有文件", "当前筛选条件下没有可处理的文件。", parent=self)
                return
            plan = self._make_plan(files, directory, prefix, tail, start)
            preview = "\n".join(
                f"{item.source.name}  →  {item.target.name}" for item in plan
            )
            if not messagebox.askyesno(
                "确认重命名", f"以下 {len(plan)} 个文件将被重命名：\n\n{preview}",
                parent=self
            ):
                return

            # 用户查看预览期间目录可能变化；变化时不执行旧预览。
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

    def clear(self):
        self.files = []
        self.directory_var.set("")
        self.file_listbox.delete(0, tk.END)
