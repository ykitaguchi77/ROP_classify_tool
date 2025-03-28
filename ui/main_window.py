import os
import cv2
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QHBoxLayout, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QSize

from utils.video_processor import VideoProcessor
from utils.image_manager import ImageManager


class MainWindow(QMainWindow):
    """
    メインウィンドウ - アプリケーションのUI構築と機能管理を行う
    """
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウの基本設定
        self.setWindowTitle("動画/画像 手動分類ツール")
        self.resize(800, 600)
        
        # モデルの初期化
        self.video_processor = VideoProcessor()
        self.image_manager = ImageManager()
        
        # シグナルの接続
        self.video_processor.progress_updated.connect(self.update_progress)
        self.video_processor.processing_completed.connect(self.on_processing_completed)
        self.video_processor.error_occurred.connect(self.show_error)
        self.image_manager.classification_changed.connect(self.update_classification_display)
        
        # UIの初期化
        self.init_ui()
        
        # キーボードショートカットの設定
        self.init_shortcuts()
    
    def init_ui(self):
        """UIコンポーネントの初期化とレイアウト設定"""
        # メインウィジェットとレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ファイル操作エリア
        file_layout = QHBoxLayout()
        self.btn_select_files = QPushButton("動画/画像 選択")
        self.btn_select_output_dir = QPushButton("JPG保存先 指定")
        self.btn_load_csv = QPushButton("CSV読込(再開)")
        
        file_layout.addWidget(self.btn_select_files)
        file_layout.addWidget(self.btn_select_output_dir)
        file_layout.addWidget(self.btn_load_csv)
        
        # ボタンの接続
        self.btn_select_files.clicked.connect(self.on_select_files)
        self.btn_select_output_dir.clicked.connect(self.on_select_output_dir)
        self.btn_load_csv.clicked.connect(self.on_load_csv)
        
        # 画像表示エリア
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 2px solid gray;")
        
        # 情報表示エリア
        info_layout = QHBoxLayout()
        self.image_info_label = QLabel("Image: 未選択 (0 / 0)")
        info_layout.addWidget(self.image_info_label)
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 分類・ナビゲーションエリア
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("<< 前へ")
        self.btn_yes = QPushButton("Yes (Y)")
        self.btn_no = QPushButton("No (N)")
        self.btn_next = QPushButton("次へ >>")
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_yes)
        nav_layout.addWidget(self.btn_no)
        nav_layout.addWidget(self.btn_next)
        
        # ボタンの接続
        self.btn_prev.clicked.connect(self.on_prev_image)
        self.btn_yes.clicked.connect(self.on_classify_yes)
        self.btn_no.clicked.connect(self.on_classify_no)
        self.btn_next.clicked.connect(self.on_next_image)
        
        # Finalizeボタンと終了ボタン
        finalize_layout = QHBoxLayout()
        self.btn_finalize = QPushButton("Finalize (CSV出力)")
        self.btn_quit = QPushButton("終了")
        finalize_layout.addWidget(self.btn_finalize)
        finalize_layout.addWidget(self.btn_quit)
        
        # ボタンの接続
        self.btn_finalize.clicked.connect(self.on_finalize)
        self.btn_quit.clicked.connect(self.close)
        
        # レイアウトの構築
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.image_label, 1)
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(nav_layout)
        main_layout.addLayout(finalize_layout)
        
        # 初期状態では一部のUIを無効化
        self.update_ui_state(False)
    
    def init_shortcuts(self):
        """キーボードショートカットの初期化"""
        # 左右矢印キーでナビゲーション
        shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        shortcut_left.activated.connect(self.on_prev_image)
        
        shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        shortcut_right.activated.connect(self.on_next_image)
        
        # Y/Nキーで分類
        shortcut_y = QShortcut(QKeySequence(Qt.Key.Key_Y), self)
        shortcut_y.activated.connect(self.on_classify_yes)
        
        shortcut_n = QShortcut(QKeySequence(Qt.Key.Key_N), self)
        shortcut_n.activated.connect(self.on_classify_no)
    
    def update_ui_state(self, has_images):
        """
        UI状態の更新
        
        Args:
            has_images (bool): 画像がロードされているかどうか
        """
        # 分類・ナビゲーション関連UIの有効/無効を切り替え
        self.btn_prev.setEnabled(has_images and self.image_manager.current_index > 0)
        self.btn_next.setEnabled(has_images and self.image_manager.current_index < len(self.image_manager.image_paths) - 1)
        self.btn_yes.setEnabled(has_images)
        self.btn_no.setEnabled(has_images)
        self.btn_finalize.setEnabled(has_images)
        self.btn_load_csv.setEnabled(has_images)
    
    def display_image(self, image_path=None):
        """
        画像を表示
        
        Args:
            image_path (str, optional): 表示する画像のパス。Noneの場合は現在選択中の画像を表示。
        """
        if image_path is None:
            image_path = self.image_manager.get_current_image()
            
        if not image_path or not os.path.exists(image_path):
            self.image_label.setText("画像がありません")
            return
            
        # 画像の読み込み
        pixmap = QPixmap(image_path)
        
        # 画像サイズの調整（アスペクト比を維持しつつ、表示エリアに収める）
        pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 画像を表示
        self.image_label.setPixmap(pixmap)
        
        # 画像情報の更新
        image_name = os.path.basename(image_path)
        current_index = self.image_manager.current_index + 1
        total_images = len(self.image_manager.image_paths)
        self.image_info_label.setText(f"Image: {image_name} ({current_index} / {total_images})")
        
        # 分類状態に応じた背景色の設定
        self.update_classification_display(self.image_manager.current_index, 
                                          self.image_manager.get_current_classification())
        
        # UI状態の更新
        self.update_ui_state(True)
    
    def update_classification_display(self, image_index, classification):
        """
        分類状態に応じた表示の更新
        
        Args:
            image_index (int): 画像のインデックス
            classification (str): 分類結果 ("Yes", "No", "")
        """
        # 現在表示中の画像の場合のみ更新
        if image_index != self.image_manager.current_index:
            return
            
        if classification == "Yes":
            self.image_label.setStyleSheet("border: 4px solid green;")
        elif classification == "No":
            self.image_label.setStyleSheet("border: 4px solid red;")
        else:
            self.image_label.setStyleSheet("border: 2px solid gray;")
    
    def update_progress(self, current, total):
        """
        進捗バーの更新
        
        Args:
            current (int): 現在の進捗値
            total (int): 全体の値
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
    
    def show_error(self, message):
        """
        エラーメッセージを表示
        
        Args:
            message (str): エラーメッセージ
        """
        QMessageBox.critical(self, "エラー", message)
    
    def show_info(self, message):
        """
        情報メッセージを表示
        
        Args:
            message (str): 情報メッセージ
        """
        QMessageBox.information(self, "情報", message)
    
    def show_warning(self, title, message):
        """
        警告メッセージを表示

        Args:
            title (str): メッセージボックスのタイトル
            message (str): 警告メッセージ
        """
        QMessageBox.warning(self, title, message)
    
    # イベントハンドラ
    def on_select_files(self):
        """動画/画像ファイル選択ダイアログを表示"""
        # 動画か画像かの選択
        options = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        choice = QMessageBox.question(self, "ファイル種別の選択", 
                                      "動画ファイルを選択しますか？\n「いいえ」を選択すると複数画像を選択できます。",
                                      options)
        
        if choice == QMessageBox.StandardButton.Yes:
            # 動画ファイルの選択
            file_path, _ = QFileDialog.getOpenFileName(
                self, "動画ファイルを選択", "",
                "動画ファイル (*.mp4 *.avi *.mov *.mkv);;すべてのファイル (*)"
            )
            
            if not file_path:
                return
                
            # メッセージを表示し、親フォルダを選択させる
            self.show_info("フレーム画像を保存する親フォルダを選択してください。\n選択したフォルダ内に動画ファイル名のフォルダが作成されます。")
            output_dir_parent = self.select_output_directory("フレーム画像を保存する親フォルダを選択")
            if not output_dir_parent:
                self.show_warning("フォルダ選択", "親フォルダが選択されませんでした。処理を中断します。")
                return

            # 動画ファイル名からフォルダ名を決定
            video_basename = os.path.splitext(os.path.basename(file_path))[0]
            output_dir_specific = os.path.join(output_dir_parent, video_basename)

            # 新しいフォルダを作成 (存在していてもエラーにしない)
            try:
                os.makedirs(output_dir_specific, exist_ok=True)
                self.show_info(f"フレーム画像は '{output_dir_specific}' に保存されます。") # 保存先をユーザーに通知
            except OSError as e:
                self.show_error(f"フォルダの作成に失敗しました: {output_dir_specific}\nエラー: {e}")
                return

            # 進捗バーの表示
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # 作成したフォルダパスを指定して動画処理を実行
            self.video_processor.extract_frames(file_path, output_dir_specific)
            
        else:
            # 複数の画像ファイルの選択
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "画像ファイルを選択", "",
                "画像ファイル (*.jpg *.jpeg *.png *.bmp);;すべてのファイル (*)"
            )
            
            if not file_paths:
                return
                
            # 作業フォルダの選択
            self.show_info("画像ファイルをコピーする作業用フォルダを選択してください。") # 画像の場合もメッセージ追加
            work_dir = self.select_output_directory("作業用フォルダを選択")
            if not work_dir:
                self.show_warning("フォルダ選択", "作業用フォルダが選択されませんでした。処理を中断します。")
                return
                
            # 画像を作業フォルダにコピー
            copied_paths = self.image_manager.copy_images_to_work_dir(file_paths, work_dir)
            
            # 画像の読み込みと表示
            self.image_manager.load_images(copied_paths)
            self.display_image()
    
    def on_select_output_dir(self):
        """JPG保存先ディレクトリの選択"""
        output_dir = self.select_output_directory("JPG保存先を選択")
        if output_dir:
            self.show_info(f"保存先ディレクトリが設定されました: {output_dir}")
    
    def select_output_directory(self, title):
        """
        ディレクトリ選択ダイアログの表示
        
        Args:
            title (str): ダイアログのタイトル
            
        Returns:
            str: 選択されたディレクトリのパス、キャンセルされた場合は空文字列
        """
        output_dir = QFileDialog.getExistingDirectory(self, title)
        return output_dir
    
    def on_processing_completed(self, frame_paths):
        """
        動画処理完了時の処理
        
        Args:
            frame_paths (list): 抽出されたフレーム画像のパスリスト
        """
        # 進捗バーを非表示
        self.progress_bar.setVisible(False)
        
        if not frame_paths:
            self.show_error("フレームの抽出に失敗しました")
            return
            
        # 画像マネージャーに抽出されたフレームを設定
        self.image_manager.load_images(frame_paths)
        
        # 最初の画像を表示
        self.display_image()
        
        # 処理完了メッセージ
        self.show_info(f"{len(frame_paths)}枚のフレームが抽出されました")
    
    def on_prev_image(self):
        """前の画像に移動"""
        if self.image_manager.prev_image():
            self.display_image()
    
    def on_next_image(self):
        """次の画像に移動"""
        if self.image_manager.next_image():
            self.display_image()
    
    def on_classify_yes(self):
        """現在の画像をYesとして分類し、次へ進む"""
        self.image_manager.set_classification("Yes")
        self.on_next_image() # 自動で次の画像へ
    
    def on_classify_no(self):
        """現在の画像をNoとして分類し、次へ進む"""
        self.image_manager.set_classification("No")
        self.on_next_image() # 自動で次の画像へ
    
    def on_load_csv(self):
        """CSVファイルを読み込み"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "CSVファイルを選択", "",
            "CSVファイル (*.csv);;すべてのファイル (*)"
        )
        
        if not file_path:
            return
            
        success, message = self.image_manager.load_csv(file_path)
        if success:
            self.show_info(message)
            # 表示を更新
            self.image_manager.go_to_image(0)  # リストの最初に移動
            self.display_image()
        else:
            self.show_error(message)
    
    def on_finalize(self):
        """分類結果をCSVに出力"""
        # 保存先ファイルの選択
        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSVファイルを保存", "",
            "CSVファイル (*.csv);;すべてのファイル (*)"
        )
        
        if not file_path:
            return
            
        # CSVファイルの拡張子を確認
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
            
        success, message = self.image_manager.save_csv(file_path)
        if success:
            self.show_info(message)
        else:
            self.show_error(message)