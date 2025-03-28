import os
import csv
import shutil
from PyQt6.QtCore import QObject, pyqtSignal


class ImageManager(QObject):
    """
    画像管理クラス - 画像ファイルの管理、分類状態の追跡を行う
    """
    
    classification_changed = pyqtSignal(int, str)  # (image_index, classification)
    
    def __init__(self):
        super().__init__()
        self.image_paths = []  # 画像ファイルのパスリスト
        self.classifications = {}  # {画像ファイル名: 分類結果("Yes", "No", "")}
        self.current_index = 0  # 現在の画像インデックス
        
    def load_images(self, image_paths):
        """
        画像パスリストを設定
        
        Args:
            image_paths (list): 画像ファイルのパスリスト
        """
        self.image_paths = image_paths
        self.current_index = 0
        
        # 初期状態では全て未分類
        self.classifications = {os.path.basename(path): "" for path in image_paths}
    
    def copy_images_to_work_dir(self, image_paths, work_dir):
        """
        指定された画像ファイルを作業ディレクトリにコピー
        
        Args:
            image_paths (list): コピー元の画像ファイルパスリスト
            work_dir (str): コピー先の作業ディレクトリ
            
        Returns:
            list: コピー後の画像ファイルパスリスト
        """
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)
            
        copied_paths = []
        for src_path in image_paths:
            filename = os.path.basename(src_path)
            dst_path = os.path.join(work_dir, filename)
            shutil.copy2(src_path, dst_path)
            copied_paths.append(dst_path)
            
        return copied_paths
    
    def get_current_image(self):
        """
        現在選択されている画像のパスを取得
        
        Returns:
            str: 画像ファイルのパス
        """
        if not self.image_paths or self.current_index < 0 or self.current_index >= len(self.image_paths):
            return None
        return self.image_paths[self.current_index]
    
    def get_current_classification(self):
        """
        現在の画像の分類状態を取得
        
        Returns:
            str: 分類結果 ("Yes", "No", "")
        """
        if not self.image_paths:
            return ""
        
        image_filename = os.path.basename(self.image_paths[self.current_index])
        return self.classifications.get(image_filename, "")
    
    def set_classification(self, classification):
        """
        現在の画像の分類状態を設定
        
        Args:
            classification (str): 分類結果 ("Yes" or "No")
        """
        if not self.image_paths:
            return
            
        image_filename = os.path.basename(self.image_paths[self.current_index])
        self.classifications[image_filename] = classification
        
        # 分類状態変更を通知
        self.classification_changed.emit(self.current_index, classification)
    
    def next_image(self):
        """
        次の画像を選択
        
        Returns:
            bool: 次の画像が存在する場合はTrue、そうでない場合はFalse
        """
        if not self.image_paths or self.current_index >= len(self.image_paths) - 1:
            return False
            
        self.current_index += 1
        return True
    
    def prev_image(self):
        """
        前の画像を選択
        
        Returns:
            bool: 前の画像が存在する場合はTrue、そうでない場合はFalse
        """
        if not self.image_paths or self.current_index <= 0:
            return False
            
        self.current_index -= 1
        return True
    
    def go_to_image(self, index):
        """
        指定インデックスの画像を選択
        
        Args:
            index (int): 選択する画像のインデックス
            
        Returns:
            bool: インデックスが有効な場合はTrue、そうでない場合はFalse
        """
        if not self.image_paths or index < 0 or index >= len(self.image_paths):
            return False
            
        self.current_index = index
        return True
    
    def load_csv(self, csv_path):
        """
        CSVファイルから分類結果を読み込む
        
        Args:
            csv_path (str): CSVファイルのパス
            
        Returns:
            tuple: (成功したかどうか, エラーメッセージ)
        """
        try:
            # CSVファイルが存在しない場合はエラー
            if not os.path.exists(csv_path):
                return False, "指定されたCSVファイルが見つかりません"
                
            loaded_classifications = {}
            
            with open(csv_path, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                
                # ヘッダーの確認
                required_fields = ['frame_index', 'image_name', 'classification']
                if not all(field in csv_reader.fieldnames for field in required_fields):
                    return False, "CSVファイルのフォーマットが正しくありません"
                
                # 各行を処理
                for row in csv_reader:
                    image_name = row['image_name']
                    classification = row['classification']
                    
                    # 分類が "Yes" または "No" または空欄(未分類)の場合のみ受け入れる
                    if classification in ["Yes", "No", ""]:
                        loaded_classifications[image_name] = classification
            
            # 読み込んだ分類結果と現在のイメージリストの整合性チェック
            current_filenames = [os.path.basename(path) for path in self.image_paths]
            csv_filenames = list(loaded_classifications.keys())
            
            # CSVに含まれるファイルが現在のリストに存在するか確認
            missing_files = [f for f in csv_filenames if f not in current_filenames]
            if missing_files:
                return False, f"CSVに含まれる画像ファイル ({len(missing_files)} 件) が現在のフォルダに見つかりません"
            
            # 分類結果を更新
            for image_name, classification in loaded_classifications.items():
                if image_name in self.classifications:
                    self.classifications[image_name] = classification
            
            return True, "CSVファイルを正常に読み込みました"
            
        except Exception as e:
            return False, f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}"
    
    def save_csv(self, csv_path):
        """
        分類結果をCSVファイルに保存
        
        Args:
            csv_path (str): 保存先CSVファイルのパス
            
        Returns:
            tuple: (成功したかどうか, エラーメッセージ)
        """
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                
                # ヘッダー行を書き込み
                csv_writer.writerow(['frame_index', 'image_name', 'classification'])
                
                # 各画像の分類結果を書き込み
                for i, image_path in enumerate(self.image_paths):
                    image_name = os.path.basename(image_path)
                    classification = self.classifications.get(image_name, "")
                    csv_writer.writerow([i+1, image_name, classification])
                    
            return True, "CSVファイルを正常に保存しました"
            
        except Exception as e:
            return False, f"CSVファイルの保存中にエラーが発生しました: {str(e)}"