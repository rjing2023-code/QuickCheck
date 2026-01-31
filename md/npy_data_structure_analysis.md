# lv2-color_obs_gpu.py 中 npy 文件读取逻辑及数据结构分析

本文档记录了 `e:\pproject\OmniStitch-GPU\lv2-color_obs_gpu.py` 代码中对于 `.npy` 文件的读取逻辑、存储的数据结构及其在拼接算法中的意义。

## 1. 读取逻辑 (Reading Logic)

代码通过 `load_external_quality_config` 函数加载外部检测数据。

- **配置路径**: 由常量 `EXTERNAL_CONFIG_DIR` 指定（例如 `E:\data\12-29_avi\npy`）。
- **文件命名**: 遵循 `Camera{r}-{c}.npy` 格式，其中 `r` (行) 和 `c` (列) 范围均为 1 到 5，对应 5x5 的相机网格。
- **加载方式**: 使用 `np.load(file_path, allow_pickle=True)` 加载。
- **存储映射**: 加载后的数据存储在 `quality_map` 字典中，键为 `cam_idx`（计算公式：`(r-1) * 5 + (c-1) + 1`），值为对应的 numpy 数组。

## 2. 数据结构 (Data Structure)

`.npy` 文件内存储的是一个多级嵌套的结构：

- **外层结构**: 一个列表或一维 numpy 数组，索引对应**帧号**。
    - 索引访问方式：`idx = frame_num - 1`（即数组的第 0 个元素对应视频/图像序列的第 1 帧）。
- **中层结构**: 每一帧对应一个列表，存储该帧中检测到的所有**目标框 (Detection Boxes)**。
- **内层结构**: 每个目标框是一个包含至少 4 个数值的列表或数组，代表坐标信息。
    - 根据代码中的使用方式（[lv2-color_obs_gpu.py:L451](file:///e:/pproject/OmniStitch-GPU/lv2-color_obs_gpu.py#L451)）：
      `pts = np.array([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]])`
    - 推断坐标意义为：`[x_min, y_min, x_max, y_max]`。

**结构示例**:
```python
# Camera1-1.npy 的逻辑结构
[
    [[x1, y1, x2, y2], [x3, y3, x4, y4]], # 第 1 帧的检测框
    [],                                   # 第 2 帧无检测
    [[x5, y5, x6, y6]],                   # 第 3 帧的一个检测框
    ...
]
```

## 3. 数据意义与用途 (Significance and Usage)

这些数据在 `GpuStitcher` 类及拼接流程中起到以下关键作用：

### 3.1 动态清晰度控制 (Quality Control)
- **高/低清切换**: 如果某个相机在当前帧有检测数据（即 `len(det_data[idx]) > 0`），该相机在该帧会被强制视为“高清”模式，不进行低采样模拟。
- **全局覆盖检测**: 代码会计算所有相机的检测框在最终画布上的位置。如果一个被设为“低清”的相机区域与任何检测框重叠，该相机的低清状态会被覆盖（Override），改为高清渲染。这确保了检测到的目标始终以最高清晰度呈现。

### 3.2 可视化 (Visualization)
- **目标框绘制**: 当 `DRAW_DETECTION_BOXES` 为 `True` 时，代码会将这些原始相机坐标系下的检测框，通过单应性矩阵和球面投影变换，转换到最终的拼接画布坐标系，并绘制绿色矩形框。

### 3.3 区域染色 (Low-res Tinting)
- 结合 `ENABLE_LOWRES_TINT`，检测数据决定了哪些区域不应该被染上“低清色”（通常为红色阴影），从而在视觉上突出高清检测区域。
