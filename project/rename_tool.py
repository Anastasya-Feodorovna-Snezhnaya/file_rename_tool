import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

r"""
本程序功能：
---------------------------------------
批量文件重命名工具
- 按用户输入的规则，对指定目录下的文件进行非递归批量重命名。
- 文件排序规则为默认 ASCII 排序。
- 用户可指定文件后缀（默认 .png），若用户输入不带点，会提示并补全。
- 重命名格式为：<前缀> + <尾部格式，其中 n 表示递增数字> + <文件后缀>。
- 用户可选择目录 / 手动输入路径。
- 文件尾部格式必须且仅包含一个 n，且不允许非法字符。
- 默认递增起点为 1，可修改为负数。
- 点击刷新按钮，可更新已选择目录下文件列表。
- 点击开始处理按钮，会显示确认窗口，列出旧名与新名。
- 支持 ASCII 排序重命名。

若 Windows 不允许的非法字符（\ / : * ? " < > |）出现在前缀或尾部格式中，程序会提示错误。
如未来文件内容格式或规则发生重大变化，需要修改当前程序。
---------------------------------------
"""

# Windows 不允许的文件名字符
INVALID_CHARS = set('\\/:*?"<>|')


class RenameTool:
    def __init__(self, root):
        self.root = root
        self.root.title("批量文件重命名工具")
        self.root.geometry("800x650")  # 窗口默认大小：宽 800，高 650

        # ---------------- 数据变量 ----------------
        self.current_dir = tk.StringVar()        # 当前选择的目录路径
        self.file_ext = tk.StringVar(value=".png")  # 文件后缀（默认 .png）
        self.rename_prefix = tk.StringVar(value="hello")  # 重命名前缀
        self.tail_format = tk.StringVar(value="(n)")  # 尾部格式
        self.start_index = tk.StringVar(value="1")    # 默认递增起点
        self.file_list = []  # 当前目录下符合后缀的文件列表

        # ---------------- 创建界面 ----------------
        self.create_widgets()

    def create_widgets(self):
        # ----- 上部：选择目录 -----
        frame_dir = tk.Frame(self.root)
        frame_dir.pack(fill="x", padx=10, pady=5)

        btn_select = tk.Button(frame_dir, text="选择目录", command=self.select_directory)
        btn_select.pack(side="left")

        entry_dir = tk.Entry(frame_dir, textvariable=self.current_dir)
        entry_dir.pack(side="left", fill="x", expand=True, padx=5)  # 输入框随窗口宽度伸缩

        # ----- 指定文件后缀 -----
        frame_ext = tk.Frame(self.root)
        frame_ext.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_ext, text="指定格式:").pack(side="left")
        combo_ext = ttk.Combobox(frame_ext, textvariable=self.file_ext, width=10)
        combo_ext["values"] = [".png", ".jpg", ".txt", ".md"]
        combo_ext.pack(side="left")
        combo_ext.bind("<FocusOut>", self.validate_ext)  # 失焦检查

        # ----- 重命名前缀 -----
        frame_prefix = tk.Frame(self.root)
        frame_prefix.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_prefix, text="重命名前缀:").pack(side="left")
        entry_prefix = tk.Entry(frame_prefix, textvariable=self.rename_prefix, width=20)
        entry_prefix.pack(side="left")
        entry_prefix.bind("<FocusOut>", self.validate_prefix)

        # ----- 尾部格式 -----
        frame_tail = tk.Frame(self.root)
        frame_tail.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_tail, text="文件前缀尾部格式:").pack(side="left")
        combo_tail = ttk.Combobox(frame_tail, textvariable=self.tail_format, width=10)
        combo_tail["values"] = ["(n)", "n", "<n>", "_{n}"]
        combo_tail.pack(side="left")
        combo_tail.bind("<FocusOut>", self.validate_tail)

        # ----- 默认递增起点 -----
        frame_start = tk.Frame(self.root)
        frame_start.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_start, text="默认递增起点:").pack(side="left")
        entry_start = tk.Entry(frame_start, textvariable=self.start_index, width=10)
        entry_start.pack(side="left")
        entry_start.bind("<FocusOut>", self.validate_start_index)

        # ----- 文件显示区域 -----
        frame_files = tk.Frame(self.root)
        frame_files.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_files, text="已选择文件:").pack(anchor="w")

        self.text_files = tk.Text(frame_files, wrap="none")
        self.text_files.pack(fill="both", expand=True)  # 文本区域随窗口伸缩

        # ----- 按钮区域 -----
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)

        btn_process = tk.Button(frame_btn, text="开始处理", command=self.process_files)
        btn_process.pack(side="left", padx=5)

        btn_refresh = tk.Button(frame_btn, text="刷新文件列表", command=self.load_files)
        btn_refresh.pack(side="left", padx=5)

        btn_clear = tk.Button(frame_btn, text="清空列表", command=self.clear_list)
        btn_clear.pack(side="left", padx=5)

    # ---------------- 校验函数 ----------------
    def validate_ext(self, event=None):
        ext = self.file_ext.get().strip()
        if not ext:
            messagebox.showerror("错误", "文件后缀不能为空")
            return
        if not ext.startswith("."):
            messagebox.showinfo("提示", f"你输入的后缀未带点，将按 {'.' + ext} 处理")
            ext = "." + ext
            self.file_ext.set(ext)

    def validate_prefix(self, event=None):
        prefix = self.rename_prefix.get().strip()
        if not prefix:
            messagebox.showerror("错误", "前缀不能为空")
            return
        if any(ch in INVALID_CHARS for ch in prefix):
            messagebox.showerror("错误", f"前缀包含非法字符: {INVALID_CHARS}")

    def validate_tail(self, event=None):
        tail_fmt = self.tail_format.get()
        if tail_fmt.count("n") != 1:
            messagebox.showerror("错误", "尾部格式必须且仅包含一个 'n'")
            return
        if any(ch in INVALID_CHARS for ch in tail_fmt):
            messagebox.showerror("错误", f"尾部格式包含非法字符: {INVALID_CHARS}")

    def validate_start_index(self, event=None):
        try:
            int(self.start_index.get())
        except ValueError:
            messagebox.showerror("错误", "递增起点必须是整数")

    # ---------------- 功能函数 ----------------
    def select_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.current_dir.set(dir_path)
            self.load_files()

    def load_files(self):
        dir_path = self.current_dir.get()
        if not os.path.isdir(dir_path):
            messagebox.showerror("错误", "目录无效")
            return

        self.validate_ext()
        ext = self.file_ext.get().strip()

        # 列出符合后缀的文件，按 ASCII 排序
        self.file_list = sorted(
            [f for f in os.listdir(dir_path) if f.endswith(ext)]
        )
        self.update_file_display()

    def update_file_display(self):
        self.text_files.delete("1.0", tk.END)
        if not self.current_dir.get():
            return
        # 第一行显示目录
        self.text_files.insert(tk.END, self.current_dir.get() + "\n")
        # 后续显示文件名
        for f in self.file_list:
            self.text_files.insert(tk.END, f + "\n")

    def process_files(self):
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件可处理")
            return

        # 统一再次校验
        self.validate_ext()
        self.validate_prefix()
        self.validate_tail()
        self.validate_start_index()

        try:
            start = int(self.start_index.get())
        except ValueError:
            return

        tail_fmt = self.tail_format.get()
        prefix = self.rename_prefix.get()
        ext = self.file_ext.get()
        dir_path = self.current_dir.get()

        # 生成预览
        preview = ""
        new_names = []
        for idx, old_name in enumerate(self.file_list, start=start):
            new_tail = tail_fmt.replace("n", str(idx))
            new_name = f"{prefix}{new_tail}{ext}"
            preview += f"{old_name}  --->  {new_name}\n"
            new_names.append(new_name)

        # 弹窗确认
        confirm = messagebox.askokcancel("确认重命名", f"以下文件将被修改:\n{preview}")
        if not confirm:
            return

        # 执行重命名
        for old_name, new_name in zip(self.file_list, new_names):
            old_path = os.path.join(dir_path, old_name)
            new_path = os.path.join(dir_path, new_name)
            os.rename(old_path, new_path)

        messagebox.showinfo("完成", "文件重命名完成")
        self.load_files()

    def clear_list(self):
        self.file_list = []
        self.current_dir.set("")
        self.text_files.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()  # 使用标准 Tk，不用拖拽功能
    app = RenameTool(root)
    root.mainloop()


"""
---------------------------------------
依赖与打包说明：

安装依赖：
- 本程序基于 tkinter（Python 内置库），无需额外安装。

打包为 exe：
- 安装 PyInstaller：
    pip install pyinstaller

- 在终端执行：
    pyinstaller --noconsole --onefile --name 批量重命名工具 rename_tool.py
-name 参数是最终生成.exe 名字，后面的参数你实际 py 文件的名字（例如 chap1/rename_tool.py）
说明：
- 生成的 exe 文件在 dist/ 目录中。
- 若要指定图标，可加参数：
    --icon your_icon.ico
---------------------------------------
"""
