# QuickCheck

QuickCheck 是一个轻量的视频标注对比与查看工具，专为校验算法结果设计。它支持批量加载视频，自动叠加对比两组 JSON 标注数据（Old vs New），并提供直方图统计功能。

## 🚀 环境配置与运行

### 1. 环境准备
确保已安装 Python 3.9 或更高版本。建议使用虚拟环境（如 venv 或 conda）来管理项目依赖。

### 2. 安装依赖
在项目根目录下运行以下命令安装所需库：
```bash
pip install -r requirements.txt
```
如果下载速度较慢，可以使用清华源镜像进行安装：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
*注：如果遇到 PyQt5 相关问题，请确保安装了适合您系统的版本。*

### 3. 运行应用
启动可视化查看器：
```bash
python labeling_app.py
```

### 4. 辅助工具
批量生成所有视频的标注统计直方图：
```bash
python batch_generate_histograms.py
```
生成的直方图图片将保存至 `histograms_output/` 文件夹。

## ✨ 功能特性

### 1. 视频浏览
- **文件夹加载**：点击界面顶部的“选择文件夹”按钮，选择包含 AVI 视频的目录。
- **快速切换**：程序会自动扫描目录下的视频文件，通过下拉框即可在不同视频间快速切换。
- **自适应缩放**：视频画面会根据窗口大小自动缩放并居中显示，无需手动调整窗口或滚动条。

### 2. 标注对比 (Old vs New)
程序会自动加载项目 `json/` 目录下的两个标注文件进行对比显示：
- **Old 数据** (`json/annotations_old.json`)：这个是运动检查的结果，显示为 **绿色半透明蒙版**。
- **New 数据** (`json/annotations_new.json`)：这个是yolo11n微调模型的检测，然后和运动检查取交集（只要有一点重叠就会画出）的结果，显示为 **黑色矩形边框**。
这使得用户可以直观地对比两个版本算法的差异。

### 3. 数据统计
- **实时直方图**：界面顶部实时显示当前视频每一帧的检测框数量分布。
  - 🟦 **蓝色柱状图**：Old 数据每一帧的框数量。
  - 🟧 **橙色折线**：New 数据每一帧的框数量。
  - 🟥 **红色虚线**：指示当前播放的帧位置。

### 4. 快捷键导航
- **A**：切换到上一帧
- **D**：切换到下一帧
- **输入框回车**：在帧号输入框输入数字后按回车，可直接跳转到指定帧

## 📂 项目结构
```
QuickCheck/
├── labeling_app.py              # 主应用程序代码
├── batch_generate_histograms.py # 批量生成直方图的辅助脚本
├── requirements.txt             # 项目依赖列表
├── json/                        # 存放标注数据的目录
│   ├── annotations_old.json     # 旧版本/基准标注数据
│   └── annotations_new.json     # 新版本/对比标注数据
├── histograms_output/           # 脚本生成的直方图输出目录
└── README.md                    # 项目说明文档
```

## 📝 许可证
本工具仅用于内部算法效果评估与校验。
