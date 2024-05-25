import tkinter as tk
from tkinter import font
import config
import console

def app():
    root = tk.Tk()
    root.title("永劫无间 乐器熟练度速刷")
    root.iconbitmap("顾清寒.ico")
    root.geometry("312x400")

    font_bold = font.Font(family="微软雅黑", size=14, weight="bold")
    font_default = font.Font(family="微软雅黑", size=14)

    tk.Label(root, text='快捷键', font=font_bold).grid(row=0, column=0)
    tk.Label(root, text='功能', font=font_bold).grid(row=0, column=1)

    index = 1
    for func, key in config.bind_keys.items():
        left = tk.Label(root, text=key, font=font_default)
        left.grid(row=index, column=0, padx=60, pady=1)
        right = tk.Label(root, text=func, font=font_default)
        right.grid(row=index, column=1, padx=10, pady=1)
        index += 1

    console.bind_hotkey()

    root.mainloop()



if __name__ == '__main__':
    app()
