import subprocess
import tkinter as tk
from tkinter import filedialog, Menu, scrolledtext, messagebox
from tkinter import ttk  # 导入ttk模块用于进度条
import fitz  # PyMuPDF
from file_process import extract_and_translate_pdf , remove_unwanted_characters
import file_process
import threading
import transapi
from tkinter import font
import os
import signal
import start
from logo import imgBase64
import base64
import socket

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
    return port

def createTempLogo():  # 处理图片
    tmp = open("temp.ico", "wb+")  # 创建temp.ico临时文件
    tmp.write(base64.b64decode(imgBase64))  # 写入img的base64
    tmp.close()  # 关闭文件

class PDFReader:
    def __init__(self, master, port):
        createTempLogo()
        self.port = port  # 将 port 作为类属性
        root.wm_iconbitmap("temp.ico")  # 使用 wm_iconbitmap 引入创建的 ico
        if os.path.exists("temp.ico"):
            os.remove("temp.ico")  # 创建 logo 后需删除临时 logo
        self.master = master
        self.master.title("I❤️Trans")
        self.pdf_document = None
        self.current_page = 0
        self.scale = 1.0  # 默认缩放比例
        #start.init(self.port)
        translation_thread = threading.Thread(target=start.run, args=(self.port,))
        translation_thread.start()
        # 默认字体大小
        self.font_size = 12
        self.text_font = font.Font(size=self.font_size)

        # 创建一个分窗
        self.paned_window = tk.PanedWindow(master, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 创建画布
        self.canvas = tk.Canvas(self.paned_window, bg="white")
        self.paned_window.add(self.canvas, minsize=200, stretch="always")  # 给画布设置标签

        # 创建文本框用于显示翻译结果（只读）
        self.text_area = scrolledtext.ScrolledText(self.paned_window, wrap=tk.WORD, font=self.text_font)
        self.text_area.config(state=tk.DISABLED)  # 设置为只读
        self.paned_window.add(self.text_area, minsize=200, stretch="always")  # 给文本框设置标签

        # 创建菜单
        self.menu = Menu(master)
        master.config(menu=self.menu)

        # 创建一个框架来容纳字号调整和缩放按钮
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 添加字号调整按钮
        self.increase_button = tk.Button(self.control_frame, text="+", command=self.increase_font_size)
        self.increase_button.pack(side=tk.RIGHT, padx=5)

        self.decrease_button = tk.Button(self.control_frame, text="-", command=self.decrease_font_size)
        self.decrease_button.pack(side=tk.RIGHT)

        # 添加缩放按钮
        self.zoom_in_button = tk.Button(self.control_frame, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack(side=tk.LEFT, padx=5)

        self.zoom_out_button = tk.Button(self.control_frame, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack(side=tk.LEFT)

        # 添加复选框选择是否展示 PDF 界面
        self.show_pdf_var = tk.BooleanVar(value=True)  # 默认显示 PDF
        self.show_pdf_checkbox = tk.Checkbutton(self.control_frame, text="Show PDF", variable=self.show_pdf_var, command=self.toggle_display)
        self.show_pdf_checkbox.pack(side=tk.LEFT)

        # 添加进度条
        self.progress_bar = ttk.Progressbar(master, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # 添加加载指示器
        self.loading_label = ttk.Label(self.control_frame, text="")  # 创建空的加载标签
        self.loading_label.pack(side=tk.LEFT, padx=10)

        # 添加取消按钮
        self.cancel_button = tk.Button(self.control_frame, text="取消", command=self.cancel_task)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button.config(state=tk.DISABLED)  # 初始状态禁用

        self.file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open PDF", command=self.load_pdf)
        self.file_menu.add_command(label="Save as TXT", command=self.save_as_txt)  # 添加保存为TXT选项
        self.file_menu.add_separator()
        #self.file_menu.add_command(label="Exit", command=master.quit)
        
        self.master.bind("<Configure>", self.on_resize)  # 绑定窗口调整大小事件
        self.master.bind("<Left>", self.previous_page)  # 绑定左箭头键
        self.master.bind("<Right>", self.next_page)    # 绑定右箭头键
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # 绑定鼠标滚轮事件
        self.canvas.bind("<ButtonPress-1>", self.start_drag)  # 绑定鼠标左键按下事件
        self.canvas.bind("<B1-Motion>", self.drag)  # 绑定拖动事件
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.drag_start_x = 0
        self.drag_start_y = 0

        self.cancel_requested = False  # 初始化取消标志

    def on_closing(self):
        """处理窗口关闭事件，确保关闭所有线程并终止程序"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.destroy()  # 关闭窗口
            os._exit(0)  # 强制终止程序，退出所有线程

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_document = fitz.open(file_path)
            self.current_page = 0
            self.master.title(f"I❤️Trans - {os.path.basename(file_path)}")  # 显示文件名
            self.display_page()

            translation_thread = threading.Thread(target=self.display_translation, args=(file_path, self.port))
            translation_thread.start()

    def toggle_display(self):
        """根据复选框状态切换显示布局"""
        if self.show_pdf_var.get():
            # 如果选中，显示PDF和翻译结果
            self.paned_window.paneconfigure(self.canvas, minsize=200)  # 确保画布有最小宽度
            self.paned_window.paneconfigure(self.text_area, minsize=200)  # 确保文本区域有最小宽度
            self.display_page()  # 显示 PDF 页面
            self.paned_window.paneconfigure(self.canvas, width=400)
        else:
            # 如果不选中，仅显示翻译结果
            self.paned_window.paneconfigure(self.canvas, minsize=0)  # 隐藏画布
            self.paned_window.paneconfigure(self.text_area, minsize=400)  # 确保文本区域宽度为400
            self.paned_window.paneconfigure(self.canvas, width=1)
            # 清空画布以节省空间
            self.canvas.delete("all")

    def save_as_txt(self):
        """将右侧文本框中的内容保存为TXT文件"""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    text_content = self.text_area.get(1.0, tk.END)  # 获取文本框中的内容
                    file.write(text_content)
                messagebox.showinfo("Success", "File saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def display_page(self):
        """显示当前 PDF 页面"""
        if self.pdf_document is not None and self.show_pdf_var.get():  # 如果复选框被选中
            # 获取画布的宽高
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # 获取 PDF 页面的尺寸
            page = self.pdf_document[self.current_page]
            rect = page.rect
            pdf_width = rect.width
            pdf_height = rect.height

            # 计算缩放比例以适应画布
            scale = self.scale * min(canvas_width / pdf_width, canvas_height / pdf_height)

            # 渲染页面图像
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            img = tk.PhotoImage(data=pix.tobytes())

            self.canvas.delete("all")  # 清空画布
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.img = img  # 保持对图像的引用以避免垃圾回收

    def display_translation(self, pdf_path, port):
        """显示逐段翻译结果"""
        self.cancel_requested = False  # 重置取消标志
        extracted_data = {}
        try:
            # 开始提取文件时显示提示信息和加载指示器
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "正在提取文件...\n")
            self.text_area.config(state=tk.DISABLED)
            self.progress_bar['value'] = 0
            self.loading_label.config(text="加载中...")  # 显示加载提示
            self.cancel_button.config(state=tk.NORMAL)  # 启用取消按钮

            # 使用提取并翻译 PDF 的函数
            result = extract_and_translate_pdf(pdf_path)

            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)

            for page_num, paragraphs in result:
                if self.cancel_requested:
                    break  # 如果用户请求取消，则终止任务

                self.progress_bar['value'] = page_num / len(result) * 100
                self.text_area.insert(tk.END, f"---------------------Page {page_num}----------------------\n")
                for paragraph in paragraphs:
                    translated_texts = transapi.translate_extracted_text(paragraph, port)
                    for original, translated in translated_texts.items():
                        translated = file_process.remove_consecutive_repeats(translated)
                        translated = remove_unwanted_characters(translated)
                        self.text_area.insert(tk.END, f"原文: {original}\n翻译: {translated}\n\n")
                self.progress_bar.update()

            self.text_area.config(state=tk.DISABLED)
            self.progress_bar['value'] = 100
            self.loading_label.config(text="")  # 移除加载提示
            self.cancel_button.config(state=tk.DISABLED)  # 禁用取消按钮

            # 播放提示音（可选）
            try:
                import winsound  # 仅适用于 Windows
                winsound.MessageBeep()  # 频率1000Hz，持续500ms
            except ImportError:
                # 对于非 Windows 系统，可以使用其他库或跳过
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Translation failed: {str(e)}")
            self.loading_label.config(text="")
            self.cancel_button.config(state=tk.DISABLED)

    def increase_font_size(self):
        self.font_size += 2
        self.text_font.configure(size=self.font_size)  # 更新字体大小

    def decrease_font_size(self):
        self.font_size -= 2
        if self.font_size < 8:  # 限制最小字体大小
            self.font_size = 8
        self.text_font.configure(size=self.font_size)  # 更新字体大小

    def zoom_in(self):
        self.scale *= 1.1  # 每次放大10%
        self.display_page()  # 重新渲染当前页面

    def zoom_out(self):
        self.scale /= 1.1  # 每次缩小10%
        self.display_page()  # 重新渲染当前页面

    def previous_page(self, event=None):
        if self.pdf_document is not None:
            if self.current_page > 0:
                self.current_page -= 1
                self.display_page()

    def next_page(self, event=None):
        if self.pdf_document is not None:
            if self.current_page < len(self.pdf_document) - 1:
                self.current_page += 1
                self.display_page()

    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件，进行上下翻页"""
        if event.delta > 0:
            self.previous_page()  # 向上滚动，上一页
        else:
            self.next_page()      # 向下滚动，下一页

    def start_drag(self, event):
        """记录鼠标拖动开始位置"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        """处理画布拖动事件"""
        self.canvas.xview_scroll(int(self.drag_start_x - event.x), "units")
        self.canvas.yview_scroll(int(self.drag_start_y - event.y), "units")
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_resize(self, event):
        """处理窗口大小变化事件"""
        self.display_page()  # 在窗口调整大小时重新渲染页面

    def cancel_task(self):
        """取消当前翻译任务"""
        self.cancel_requested = True  # 设置取消标志
        self.loading_label.config(text="取消中...")
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "任务已取消。\n")
        self.text_area.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.cancel_button.config(state=tk.DISABLED)  # 禁用取消按钮
        self.loading_label.config(text="")  # 移除加载提示

if __name__ == "__main__":
    root = tk.Tk()
    free_port = get_free_port()
    pdf_reader = PDFReader(root, free_port)
    root.mainloop()
