import shutil
import configparser
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
from ctypes import windll

#获取屏幕大小
def get_screen_size():
    return windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

# 获取Windows当前的屏幕缩放系数
def get_scale_factor():
    return windll.shcore.GetScaleFactorForDevice(0) / 100

# 获取缩放后的尺寸
def scale(size):
    return int (size * windll.shcore.GetScaleFactorForDevice(0) / 100)

# 获取窗口居中坐标
def center_xy(width, height):
    # 获取屏幕的宽度和高度
    screen_width, screen_height = get_screen_size()
    # 计算窗口居中的坐标
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    return x, y

class App():
    def __init__(self, config_path="config.ini"):
        self.main_window = tk.Tk()
        self.main_window.title("文件备份工具")
        self.uiset_window()
        self.add_buttons()

        self.config_path = config_path
        self.conf = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.conf.read(self.config_path)
        else:
            messagebox.showinfo("提示", "配置文件不存在，请设置备份路径")
            self.configure()

    def add_buttons(self):
        button_cfg = tk.Button(self.main_window, text="设置", command=self.configure)
        button_backup = tk.Button(self.main_window, text="备份", command=self.backup)
        button_restore = tk.Button(self.main_window, text="恢复", command=self.restore)
        button_cfg.pack(expand=True)
        button_backup.pack(expand=True)
        button_restore.pack(expand=True)
        button_font = tkfont.nametofont("TkDefaultFont").copy()
        # font_size = 15
        button_font.configure(family='Microsoft YaHei', size=button_font.cget('size') * 2)
        button_cfg.configure(font=button_font)
        button_backup.configure(font=button_font)
        button_restore.configure(font=button_font)

    def uiset_window(self):
        # 设置字体            
        default_font = tkfont.nametofont("TkDefaultFont")
        font_size = 10
        default_font.configure(family='Microsoft YaHei', size=font_size)
        self.main_window.option_add('*Font', default_font)
        
        # 缩放界面
        window_width, window_height = map(scale, (320, 240))
        x, y = center_xy(window_width, window_height)
        # 设置分辨率和坐标
        self.main_window.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")

    def configure(self):
        if not self.conf.has_section('directory'):
            self.conf.add_section('directory')
            self.conf.set('directory', 'auto_save', '')
            self.conf.set('directory', 'backup', '')
        self.cfg_window = tk.Toplevel(self.main_window)
        self.cfg_window.focus_set()
        self.cfg_window.bind("<Return>", lambda event:self.write_cfg())
        self.cfg_window.bind("<Escape>", lambda event:self.cfg_window.destroy())
        self.cfg_window.title("设置")
        width, height = map(scale, (500, 150))
        x, y = center_xy(width, height)
        self.cfg_window.geometry(f"{width}x{height}+{x}+{y}")
        self.auto_save_getter = dir_getter(self.cfg_window, "自动存档路径:", self.conf.get('directory', 'auto_save'), 0)
        self.backup_getter = dir_getter(self.cfg_window, "备份存档路径:", self.conf.get('directory', 'backup'), 1)
        button = tk.Button(self.cfg_window, text="确定", command=self.write_cfg)
        button.grid(row=3, pady=10, column=1, columnspan=2)
    def write_cfg(self):
        self.conf.set('directory', 'auto_save', self.auto_save_getter.get())
        self.conf.set('directory', 'backup', self.backup_getter.get())
        with open(self.config_path, 'w') as configfile:
            self.conf.write(configfile)
        self.cfg_window.destroy()
    def backup(self):
        dir = self.conf.get('directory', 'auto_save')
        latest = 0
        auto_saved = 'ArchiveSaveFile.1.sav'
        for file in os.listdir(dir):
            path = os.path.join(dir, file)
            if file.startswith('ArchiveSaveFile'):
                if os.path.getmtime(path) > latest:
                    latest = os.path.getmtime(path)
                    auto_saved = file
        my_backup = filedialog.asksaveasfilename(title="另存为",
                                                 initialdir=self.conf.get('directory', 'backup'),
                                                 defaultextension='.sav')
        if my_backup:
            shutil.copy2(os.path.join(dir, auto_saved), my_backup)

    def restore(self):
        existed_archives = [f for f in os.listdir(self.conf.get('directory', 'auto_save')) if f.startswith('ArchiveSaveFile')]
        existed_number = set(map(lambda x: int(x.split('.')[1]), existed_archives))
        available_number = set(range(1, 11)) - existed_number
        files_to_restore = filedialog.askopenfilenames(title=f"请选择要恢复的存档(最多{len(available_number)}个)",
                                               initialdir=self.conf.get('directory', 'backup'),
                                               defaultextension='.sav')
        for file, num in zip(files_to_restore, available_number):
            shutil.copy2(file, os.path.join(self.conf.get('directory', 'auto_save'), f'ArchiveSaveFile.{num}.sav'))

class dir_getter:
    def __init__(self, master=None, text="", init_val="", grid_row=0):
        self.root = master
        self.text = text
        self.label = tk.Label(self.root, text=text)
        self.label.grid(row=grid_row, column=0, padx=scale(10), pady=scale(10))
        self.entry = tk.Entry(self.root)
        self.entry.config(width=40)
        self.entry.grid(row=grid_row, column=1, padx=scale(10))
        self.entry.insert(0, init_val)
        self.button = tk.Button(self.root, text='浏览', command=self.set)
        self.button.grid(row=grid_row, column=2, padx=scale(10))
    def get(self):
        return self.entry.get()
    def set(self):
        path = filedialog.askdirectory(title="请选择" + self.text, parent=self.root)
        if path:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, path)

if __name__ == '__main__':
    # 调用Windows操作系统API，启动进程dpi感知，解决高dpi屏幕字体模糊问题
    windll.shcore.SetProcessDpiAwareness(1)
    app = App()
    app.main_window.mainloop()
