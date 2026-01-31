import sys
import cv2
import os
import json
import numpy as np


# 本项目的作用：
# 1. 提供一个可视化的工具，用于查看和分析视频中的运动性检测结果
# 2. 允许用户加载旧版和新版的 JSON 文件，用于对比分析
# 3. 提供帧导航功能，用户可以通过 A/D 键或输入帧号来切换视频帧
# 4. 显示旧版数据的绿色半透明蒙版和新版数据的黑色矩形框
# 5. 绘制红色十字和延长虚线，用于指示当前帧的位置
# 6. 显示直方图，展示旧版和新版数据在每帧中的框数量

# Adjust import order: Import PyQt5 before matplotlib to avoid ImportError
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QLineEdit, QMessageBox, QScrollArea, QSizePolicy, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap, QIntValidator, QPainter, QPen, QColor, QBrush

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnnotatedImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mouse_pos = None
        self.old_annotations = []
        self.new_annotations = []
        self.parent_ref = parent

    def set_annotations(self, old_annots, new_annots):
        self.old_annotations = old_annots or []
        self.new_annotations = new_annots or []
        self.update()

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        pixmap = self.pixmap()
        if not pixmap:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算缩放比例和偏移量
        w_widget = self.width()
        h_widget = self.height()
        w_img = pixmap.width()
        h_img = pixmap.height()

        if w_img == 0 or h_img == 0:
            return

        scale = min(w_widget / w_img, h_widget / h_img)
        w_dest = int(w_img * scale)
        h_dest = int(h_img * scale)
        dx = int((w_widget - w_dest) / 2)
        dy = int((h_widget - h_dest) / 2)

        # 绘制图片
        target_rect = QRect(dx, dy, w_dest, h_dest)
        painter.drawPixmap(target_rect, pixmap)
        
        # 绘制十字光标 (保留展示逻辑)
        if self.mouse_pos is not None and 0 <= self.mouse_pos.x() < self.width() and 0 <= self.mouse_pos.y() < self.height():
            pen_cross = QPen(QColor(255, 255, 255))
            pen_cross.setWidth(2)
            painter.setPen(pen_cross)
            mx, my = self.mouse_pos.x(), self.mouse_pos.y()
            painter.drawLine(mx-5, my, mx+5, my)
            painter.drawLine(mx, my-5, mx, my+5)
            
            pen_dash = QPen(QColor(220, 220, 220))
            pen_dash.setStyle(Qt.DashLine)
            pen_dash.setWidth(1)
            painter.setPen(pen_dash)
            painter.drawLine(0, my, self.width(), my)
            painter.drawLine(mx, 0, mx, self.height())
        
        # 绘制 Old Annotations (绿色蒙版)
        if self.old_annotations:
            # 绿色填充，带透明度
            brush = QBrush(QColor(0, 255, 0, 80)) # R, G, B, Alpha
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            for b in self.old_annotations:
                if len(b) >= 4:
                    x1, y1, x2, y2 = b[:4]
                    # 坐标变换
                    x1 = int(x1 * scale + dx)
                    y1 = int(y1 * scale + dy)
                    x2 = int(x2 * scale + dx)
                    y2 = int(y2 * scale + dy)
                    
                    painter.drawRect(x1, y1, x2 - x1, y2 - y1)

        # 绘制 New Annotations (黑框)
        if self.new_annotations:
            pen_box = QPen(Qt.black)
            pen_box.setWidth(2)
            painter.setPen(pen_box)
            painter.setBrush(Qt.NoBrush)
            for b in self.new_annotations:
                if len(b) >= 4:
                    x1, y1, x2, y2 = b[:4]
                    # 坐标变换
                    x1 = int(x1 * scale + dx)
                    y1 = int(y1 * scale + dy)
                    x2 = int(x2 * scale + dx)
                    y2 = int(y2 * scale + dy)
                    
                    painter.drawRect(x1, y1, x2 - x1, y2 - y1)
    
    def enterEvent(self, event):
        self.setCursor(Qt.BlankCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

class VideoLabeler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuickLabeling - Viewer Mode")
        self.resize(1600, 1200)

        # 状态变量
        self.video_cap = None
        self.video_path = None
        self.video_folder = None
        self.camera_name = None
        
        self.total_frames = 0
        self.current_frame_idx = 0
        
        # 直方图相关
        self.ax = None
        self.canvas = None
        self.current_frame_line = None
        
        # 两个 JSON 标注数据
        self.annotations_old = {}
        self.annotations_new = {}

        # 自动加载默认的 JSON 文件
        self.load_default_annotations()

        # 初始化 UI
        self.init_ui()

    def load_default_annotations(self):
        # 默认路径
        base_dir = os.getcwd()
        old_path = os.path.join(base_dir, "json", "annotations_old.json")
        new_path = os.path.join(base_dir, "json", "annotations_new.json")

        try:
            if os.path.exists(old_path):
                with open(old_path, "r", encoding="utf-8") as f:
                    self.annotations_old = json.load(f)
            else:
                print(f"Warning: {old_path} not found.")
                
            if os.path.exists(new_path):
                with open(new_path, "r", encoding="utf-8") as f:
                    self.annotations_new = json.load(f)
            else:
                print(f"Warning: {new_path} not found.")
        except Exception as e:
            print(f"Error loading default annotations: {e}")

    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 选择文件夹按钮
        self.btn_select_folder = QPushButton("选择文件夹 (Select Folder)")
        self.btn_select_folder.clicked.connect(self.select_video_folder)
        control_layout.addWidget(self.btn_select_folder)

        # 视频下拉框
        self.video_combo = QComboBox()
        self.video_combo.setMinimumWidth(300)
        self.video_combo.currentIndexChanged.connect(self.on_video_combo_changed)
        control_layout.addWidget(self.video_combo)

        # 帧数显示和跳转
        control_layout.addStretch()
        
        control_layout.addWidget(QLabel("帧号:"))
        
        self.input_frame = QLineEdit()
        self.input_frame.setValidator(QIntValidator())
        self.input_frame.setFixedWidth(80)
        self.input_frame.returnPressed.connect(self.jump_to_frame_from_input)
        control_layout.addWidget(self.input_frame)

        self.label_total_frames = QLabel("/ 0")
        control_layout.addWidget(self.label_total_frames)

        self.btn_jump = QPushButton("跳转 (Go)")
        self.btn_jump.clicked.connect(self.jump_to_frame_from_input)
        control_layout.addWidget(self.btn_jump)

        control_layout.addStretch()

        # 说明标签
        tips_label = QLabel("快捷键: 'A' 上一帧, 'D' 下一帧")
        tips_label.setStyleSheet("color: gray;")
        control_layout.addWidget(tips_label)

        control_layout.addStretch()
        
        # 移除标注状态显示，改为显示加载状态
        self.label_status = QLabel("Ready")
        control_layout.addWidget(self.label_status)

        main_layout.addLayout(control_layout)

        # 1.5 直方图区域
        fig = Figure(figsize=(5, 1.5), dpi=100)
        self.canvas = FigureCanvas(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.canvas.setFixedHeight(150)
        self.ax = fig.add_subplot(111)
        self.ax.set_title("Detection Boxes Histogram (Old vs New)")
        self.ax.set_xlabel("Frame")
        self.ax.set_ylabel("Count")
        fig.tight_layout()
        
        main_layout.addWidget(self.canvas)

        # 2. 图片展示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_label = AnnotatedImageLabel(self)
        self.image_label.setText("请加载视频文件和 JSON 文件")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.scroll_area.setWidget(self.image_label)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.scroll_area, 3)
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setMinimumWidth(320)
        self.help_text.setText(
            "QuickLabeling Viewer Mode\n\n"
            "工作流程\n"
            "1. 点击“选择文件夹”选择包含AVI视频的文件夹\n"
            "2. 使用下拉框切换不同的视频\n"
            "3. 程序会自动加载项目中的 Old/New JSON\n"
            "4. 使用 A/D 或输入帧号进行导航\n\n"
            "显示说明\n"
            "- Old 数据：使用运动性检测结果绘制绿色半透明蒙版\n"
            "- New 数据：使用yolo11n微调模型检测结果（与运动性检测结果取交集，只要有一点重叠就会画出）绘制黑色矩形框\n"
            "- 鼠标指示：红色十字与延长虚线\n"
            "- 直方图：显示 Old(蓝色) 和 New(橙色) 的每帧框数量\n\n"
            "快捷键\n"
            "- A：上一帧\n"
            "- D：下一帧\n"
            "- 回车：在帧号输入框中回车跳转\n"
        )
        content_layout.addWidget(self.help_text, 1)
        main_layout.addLayout(content_layout)

    def load_json_file(self, type_name):
        file_path, _ = QFileDialog.getOpenFileName(self, f"选择 {type_name.upper()} JSON 文件", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if type_name == "old":
                    self.annotations_old = data
                    QMessageBox.information(self, "成功", "Old JSON 加载成功！")
                else:
                    self.annotations_new = data
                    QMessageBox.information(self, "成功", "New JSON 加载成功！")
                
                self.update_histogram()
                if self.video_cap:
                    self.show_frame(self.current_frame_idx)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载 JSON 失败: {e}")

    def update_histogram(self):
        # 清空图表
        self.ax.clear()
        
        if self.total_frames <= 0:
            self.canvas.draw()
            return

        frames = list(range(1, self.total_frames + 1))
        
        # 获取 Old 数量
        counts_old = [0] * self.total_frames
        if self.annotations_old and self.camera_name:
            cam_data = self.annotations_old.get(self.camera_name, {})
            for f_idx in range(self.total_frames):
                key = str(f_idx + 1)
                if key in cam_data:
                    counts_old[f_idx] = len(cam_data[key])
        
        # 获取 New 数量
        counts_new = [0] * self.total_frames
        if self.annotations_new and self.camera_name:
            cam_data = self.annotations_new.get(self.camera_name, {})
            for f_idx in range(self.total_frames):
                key = str(f_idx + 1)
                if key in cam_data:
                    counts_new[f_idx] = len(cam_data[key])

        # 绘制直方图
        # Old 用蓝色柱状图
        self.ax.bar(frames, counts_old, width=1.0, color='skyblue', label='Old', alpha=0.6)
        # New 用橙色线条或柱状图 (这里用细柱或阶梯线)
        self.ax.plot(frames, counts_new, color='orange', label='New', linewidth=1.5)
        
        self.ax.set_title("Detection Boxes Histogram")
        self.ax.set_xlabel("Frame Number")
        self.ax.set_ylabel("Box Count")
        self.ax.set_xlim(0, self.total_frames + 1)
        self.ax.legend(loc='upper right')

        # 当前帧指示线
        self.current_frame_line = self.ax.axvline(x=self.current_frame_idx + 1, color='red', linewidth=2, linestyle='--')
        self.canvas.draw()

    def select_video_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder_path:
            self.video_folder = folder_path
            
            # 扫描 .avi 文件
            try:
                videos = [f for f in os.listdir(folder_path) if f.lower().endswith('.avi')]
                videos.sort()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法扫描文件夹: {e}")
                return

            if not videos:
                QMessageBox.warning(self, "提示", "该文件夹下没有找到 .avi 文件")
                self.video_combo.clear()
                return

            self.video_combo.blockSignals(True)
            self.video_combo.clear()
            self.video_combo.addItems(videos)
            self.video_combo.blockSignals(False)
            
            # 自动加载第一个
            if self.video_combo.count() > 0:
                self.video_combo.setCurrentIndex(0)
                # 手动触发加载
                self.on_video_combo_changed(0)

    def on_video_combo_changed(self, index):
        if index < 0 or not self.video_folder:
            return
        video_name = self.video_combo.itemText(index)
        full_path = os.path.join(self.video_folder, video_name)
        self.load_video_file(full_path)

    def load_video_file(self, file_path):
        if file_path:
            self.video_path = file_path
            self.camera_name = os.path.basename(file_path)
            self.video_cap = cv2.VideoCapture(file_path)
            if not self.video_cap.isOpened():
                QMessageBox.critical(self, "错误", "无法打开视频文件！")
                return
            
            self.total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.label_total_frames.setText(f"/ {self.total_frames}")
            self.current_frame_idx = 0
            
            # 更新直方图（因为 camera_name 变了）
            self.update_histogram()

            # 显示第一帧
            self.show_frame(self.current_frame_idx)
            self.update_frame_input_display()
            
            self.setFocus()
            
            # 更新状态栏显示加载情况
            status_text = []
            if self.annotations_old:
                status_text.append("Old JSON Loaded")
            else:
                status_text.append("Old JSON Missing")
                
            if self.annotations_new:
                status_text.append("New JSON Loaded")
            else:
                status_text.append("New JSON Missing")
            
            self.label_status.setText(" | ".join(status_text))

    def show_frame(self, frame_idx):
        if self.video_cap is None or not self.video_cap.isOpened():
            return

        if frame_idx < 0:
            frame_idx = 0
        elif frame_idx >= self.total_frames:
            frame_idx = self.total_frames - 1

        self.current_frame_idx = frame_idx
        
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_idx)
        ret, frame = self.video_cap.read()
        
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))
            self.image_label.update()
            
            self.update_frame_input_display()

            # 更新直方图指示器
            if self.current_frame_line:
                self.current_frame_line.set_xdata([self.current_frame_idx + 1])
                self.canvas.draw_idle()
            
            # 获取当前帧的 Old 和 New 标注
            old_boxes = self.get_frame_annotations(self.annotations_old)
            new_boxes = self.get_frame_annotations(self.annotations_new)
            
            self.image_label.set_annotations(old_boxes, new_boxes)
        else:
            self.image_label.setText(f"无法读取第 {frame_idx + 1} 帧")

    def get_frame_annotations(self, annotations_dict):
        if not self.camera_name or not annotations_dict:
            return []
        cam = annotations_dict.get(self.camera_name, {})
        return cam.get(str(self.current_frame_idx + 1), [])

    def update_frame_input_display(self):
        self.input_frame.setText(str(self.current_frame_idx + 1))

    def jump_to_frame_from_input(self):
        if not self.video_cap:
            return
            
        text = self.input_frame.text()
        if text.isdigit():
            target_frame = int(text) - 1
            self.show_frame(target_frame)
        
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.video_cap:
            return

        # A 键：上一帧
        if event.key() == Qt.Key_A:
            if self.current_frame_idx > 0:
                self.show_frame(self.current_frame_idx - 1)
        
        # D 键：下一帧
        elif event.key() == Qt.Key_D:
            if self.current_frame_idx < self.total_frames - 1:
                self.show_frame(self.current_frame_idx + 1)
        
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoLabeler()
    window.show()
    sys.exit(app.exec_())
