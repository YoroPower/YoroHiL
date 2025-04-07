from imports import *

chinese = {
    'global.quitConfirmation': u'确定关闭?',
}


def run_webview():
    icon_path = "/my-app/out/favicon.ico"
    port = os.getenv("MAIN_PORT", 12233)
    webview.create_window('InLoop测试',
                          f'http://localhost:{port}',
                          text_select=True,  # 可复制文字
                          zoomable=True,  # 可调整大小
                          confirm_close=True,  # 关闭时提示
                          # background_color='#333333'
                          )

    webview.start(gui="gtk", icon=icon_path, localization=chinese)
