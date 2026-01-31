# QuickLabeling - 视频标注工具

QuickLabeling 是一个轻量的视频标注工具，支持加载视频、叠加 NPY 检测框、显示帧分布直方图、手动框选标注并持久化保存，满足快速浏览与定位高密度场景的需求。

## 功能特性
- 加载本地视频并以原分辨率显示（推荐图像尺寸 1440×1080）。
- 加载 NPY 文件，按帧叠加淡绿色蒙版框（检测框来源）。
- 顶部直方图展示每帧的检测框数量，并以橙色点标记“已标注”帧；红色虚线表示当前帧。
- 手动框选标注：在画面中拖拽左键绘制品红色虚线框；支持删除上一条标注。
- 标注数据自动保存到本地文件，按“相机名称（视频文件名）+帧号”组织。
- 快速跳转：上一帧/下一帧、输入帧号跳转、上一标注帧/下一标注帧。
- 内置右侧帮助面板，概览工作流程与快捷键。

## 下载与运行
- 从 GitHub Releases 下载打包版本（压缩包或可执行程序），解压后直接运行应用。
- 首次启动后：
  - 点击“加载视频”选择待标注视频
  - 可选：点击“加载 NPY”叠加检测框并生成直方图
  - 使用 A/D 或输入帧号导航；拖拽左键框选进行标注；按 Q 删除当前帧最后一次标注

## 源码部署（pip）
- 环境准备：
  - 安装 Python 3.9+（建议 3.10 或以上）
  - Windows 用户建议用 PowerShell/命令提示符
- 安装依赖并运行：
  ```
  git clone <your-repo-url>
  cd QuickLabeling
  pip install -r requirements.txt
  python labeling_app.py
  ```
- 如下载缓慢可使用镜像源：
  ```
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- 常见问题：
  - 若提示 PyQt5/Qt 相关导入问题，执行：
    ```
    pip install PyQt5==5.15.11
    ```
  - 若 OpenCV 报错，执行：
    ```
    pip install opencv-python
    ```

## 文件与数据
- 主程序： [labeling_app.py](file:///e:/pproject/QuickLabeling/labeling_app.py)
- NPY 数据结构说明： [npy_data_structure_analysis.md](file:///e:/pproject/QuickLabeling/npy_data_structure_analysis.md)
- 标注持久化文件： `annotations.json`
  - 结构示意：
    ```
    {
      "CameraVideoName.mp4": {
        "1": [[x1, y1, x2, y2], ...],
        "2": [...],
        ...
      }
    }
    ```
  - 键为“相机名称”（即视频文件名），帧号使用字符串（1-based）。
  - 值为该帧的矩形框列表，坐标格式：左上角 `(x1, y1)`，右下角 `(x2, y2)`。

## 交互与显示约定
- 图像区域：
  - 用户标注：品红色虚线框
  - NPY 检测框：绿色淡蒙版
  - 鼠标指示：白色十字与延长虚线（图像内隐藏鼠标箭头）
- 直方图：
  - 蓝色柱：每帧检测框数量
  - 橙色点：已标注帧（显示帧号）
  - 红色虚线：当前帧位置

## 快捷键
- A：上一帧
- D：下一帧
- Q：删除当前帧最后一次标注
- 回车：在帧号输入框中回车跳转
- 按钮：上一标注帧 / 下一标注帧（位于顶部右侧）

## 常见问题
- NPY 文件与视频帧的对应关系：NPY 第 0 个元素对应视频第 1 帧，索引访问需使用 `frame_num - 1`。
- 若直方图未显示，请确保已加载视频或 NPY 文件（用于计算总帧数或帧计数）。
- 标注文件按视频名称区分，确保加载同名视频可自动恢复历史标注。

## 许可证
本工具用于视频标注与评估用途。
