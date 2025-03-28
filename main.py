import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """
    アプリケーションのエントリーポイント
    """
    # PyQt6 アプリケーションの初期化
    app = QApplication(sys.argv)
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    # イベントループの開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()