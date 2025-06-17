import os
import sys


def GetPath():
    # 动态获取当前.exe所在的目录，确保能正确加载资源文件
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件运行，'frozen' 属性会被设置
        app_dir = sys._MEIPASS
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
    return app_dir