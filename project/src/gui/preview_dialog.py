import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont


def show_rename_preview(parent, title, plan, initial_geometry="", on_geometry_change=None):
    """显示可调整大小的双列重命名预览；返回用户是否确认。"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent.winfo_toplevel())
    dialog.resizable(True, True)

    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    max_width = max(480, screen_width // 2)
    max_height = max(360, int(screen_height * 0.78))
    dialog.maxsize(max_width, max_height)
    dialog.minsize(min(520, max_width), min(320, max_height))

    font = tkfont.nametofont("TkDefaultFont")
    source_width = max([font.measure("原文件名")] + [
        font.measure(item.source.name) for item in plan
    ]) + 28
    target_width = max([font.measure("新文件名")] + [
        font.measure(item.target.name) for item in plan
    ]) + 28
    desired_width = source_width + target_width + 90
    initial_width = min(max(640, desired_width), max_width)
    initial_height = min(max(360, min(680, 150 + len(plan) * 26)), max_height)

    if initial_geometry:
        try:
            dialog.geometry(initial_geometry)
        except tk.TclError:
            dialog.geometry(f"{initial_width}x{initial_height}")
    else:
        dialog.geometry(f"{initial_width}x{initial_height}")

    container = ttk.Frame(dialog, padding=10)
    container.pack(fill="both", expand=True)
    ttk.Label(
        container,
        text=f"共 {len(plan)} 个文件。可拖动窗口边缘调整大小；列宽不足时可使用底部滚动条。",
    ).pack(anchor="w", pady=(0, 8))

    table_frame = ttk.Frame(container)
    table_frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(
        table_frame, columns=("source", "target"), show="headings",
        selectmode="extended"
    )
    tree.heading("source", text="原文件名")
    tree.heading("target", text="新文件名")
    available_column_width = max(160, (initial_width - 110) // 2)
    tree.column("source", width=min(source_width, available_column_width), minwidth=80, stretch=True)
    tree.column("target", width=min(target_width, available_column_width), minwidth=80, stretch=True)

    vertical = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    for item in plan:
        tree.insert("", "end", values=(item.source.name, item.target.name))

    result = {"confirmed": False}

    def finish(confirmed):
        if on_geometry_change:
            on_geometry_change(dialog.geometry())
        result["confirmed"] = confirmed
        dialog.grab_release()
        dialog.destroy()

    buttons = ttk.Frame(container)
    buttons.pack(fill="x", pady=(10, 0))
    ttk.Button(buttons, text="取消", command=lambda: finish(False)).pack(side="right")
    ttk.Button(buttons, text="确认重命名", command=lambda: finish(True)).pack(
        side="right", padx=(0, 8)
    )
    dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    dialog.grab_set()
    dialog.wait_window()
    return result["confirmed"]
