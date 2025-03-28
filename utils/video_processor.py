import cv2
import os
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal


class VideoProcessor(QObject):
    """動画処理クラス - 動画ファイルからフレームを抽出しJPG画像として保存する"""
    
    progress_updated = pyqtSignal(int, int)  # (current_frame, total_frames)
    processing_completed = pyqtSignal(list)  # フレーム画像のパスリスト
    error_occurred = pyqtSignal(str)         # エラーメッセージ
    
    def __init__(self):
        super().__init__()
        
    def extract_frames(self, video_path, output_dir):
        """
        動画ファイルからすべてのフレームを抽出しJPG画像として保存
        
        Args:
            video_path (str): 動画ファイルのパス
            output_dir (str): 抽出したフレームの保存先ディレクトリ
            
        Returns:
            list: 保存されたフレーム画像のパスリスト
        """
        try:
            # 出力ディレクトリの存在確認、なければ作成
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # 動画ファイルを開く
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.error_occurred.emit("動画ファイルを開けませんでした")
                return []
                
            # 動画ファイルの情報取得
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                self.error_occurred.emit("動画のフレーム数を取得できませんでした")
                return []
                
            # 動画ファイル名（拡張子なし）を取得
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            
            # 全フレームを抽出
            frame_paths = []
            frame_index = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_index += 1
                # ファイル名: [ベース名]_[フレーム番号(0埋め4桁)].jpg
                frame_filename = f"{base_name}_{frame_index:04d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # JPG画像として保存
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                
                # 進捗状況を通知
                self.progress_updated.emit(frame_index, total_frames)
            
            # 後処理
            cap.release()
            
            # 処理完了を通知
            self.processing_completed.emit(frame_paths)
            return frame_paths
            
        except Exception as e:
            self.error_occurred.emit(f"フレーム抽出中にエラーが発生しました: {str(e)}")
            return []