import os
import json
import cv2
import matplotlib.pyplot as plt
import numpy as np

# 本脚本的作用：
# 1. 批量生成视频的直方图，展示不同数据在每帧中的框数量
# 2. 生成的直方图将保存为 PNG 格式，文件名与视频文件相同

def main():
    # 配置路径
    video_folder = r"E:\data\12-29_avi"
    project_root = r"e:\pproject\QuickCheck"
    old_json_path = os.path.join(project_root, "json", "annotations_old.json")
    new_json_path = os.path.join(project_root, "json", "annotations_new.json")
    output_folder = os.path.join(project_root, "histograms_output")

    # 创建输出目录
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")

    # 加载 JSON 数据
    print("Loading JSON files...")
    annotations_old = {}
    annotations_new = {}

    if os.path.exists(old_json_path):
        with open(old_json_path, "r", encoding="utf-8") as f:
            annotations_old = json.load(f)
        print(f"Loaded Old JSON from {old_json_path}")
    else:
        print(f"Warning: Old JSON not found at {old_json_path}")

    if os.path.exists(new_json_path):
        with open(new_json_path, "r", encoding="utf-8") as f:
            annotations_new = json.load(f)
        print(f"Loaded New JSON from {new_json_path}")
    else:
        print(f"Warning: New JSON not found at {new_json_path}")

    # 扫描视频文件
    if not os.path.exists(video_folder):
        print(f"Error: Video folder not found: {video_folder}")
        return

    video_files = [f for f in os.listdir(video_folder) if f.lower().endswith('.avi')]
    video_files.sort()

    if not video_files:
        print("No .avi files found in the video folder.")
        return

    print(f"Found {len(video_files)} video files. Starting processing...")

    for i, video_file in enumerate(video_files):
        print(f"[{i+1}/{len(video_files)}] Processing {video_file}...")
        video_path = os.path.join(video_folder, video_file)
        
        # 获取视频信息
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"  Error: Could not open video {video_path}")
            continue
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames <= 0:
            print("  Warning: Invalid frame count (0). Skipping.")
            continue

        # 准备数据
        frames = list(range(1, total_frames + 1))
        counts_old = [0] * total_frames
        counts_new = [0] * total_frames

        # 填充 Old 数据
        if annotations_old:
            cam_data = annotations_old.get(video_file, {})
            for f_idx in range(total_frames):
                key = str(f_idx + 1)
                if key in cam_data:
                    counts_old[f_idx] = len(cam_data[key])

        # 填充 New 数据
        if annotations_new:
            cam_data = annotations_new.get(video_file, {})
            for f_idx in range(total_frames):
                key = str(f_idx + 1)
                if key in cam_data:
                    counts_new[f_idx] = len(cam_data[key])

        # 确定 Y 轴范围
        max_count = 0
        if counts_old:
            max_count = max(max_count, max(counts_old))
        if counts_new:
            max_count = max(max_count, max(counts_new))
        
        # 纵轴最小值固定为5，当框数量有更大的就固定为最大值
        y_limit = max(5, max_count)
        # 稍微加一点余量，如果是正好整数，可以考虑 +1 让图好看点，但用户说“固定为最大值”，这里严格按照最大值来
        # 如果 max_count > 5，y_limit = max_count
        # 为了避免顶格不好看，通常 matplotlib 默认会自动调整，但如果要强制：
        # plt.ylim(0, y_limit) 
        # 这里如果 max_count 是 5，ylim 是 5。如果 max_count 是 10，ylim 是 10。
        
        # 绘图
        plt.figure(figsize=(10, 6))
        plt.bar(frames, counts_old, width=1.0, color='skyblue', label='Old', alpha=0.6)
        plt.plot(frames, counts_new, color='orange', label='New', linewidth=1.5)
        
        plt.title(f"Detection Boxes Histogram - {video_file}")
        plt.xlabel("Frame Number")
        plt.ylabel("Box Count")
        plt.xlim(0, total_frames + 1)
        
        # 设置 Y 轴范围
        # 注意：matplotlib 的 ylim 如果设为 (0, 5)，那么 5 就在最顶端。
        # 如果要让最大值能显示出来，通常建议稍微多一点点，或者就正好。
        # 这里按照用户“固定为最大值”的字面意思，设为 y_limit。
        # 但是为了防止顶部的线被遮挡，如果是 plot 的线，可能刚好压线。
        # 不过既然用户这么要求，先尝试精确设置。
        # 为了保证刻度整数显示，可以使用 MaxNLocator
        plt.ylim(0, y_limit + (0.1 if y_limit > 5 else 0)) # 稍微加一点点防止压线，或者就直接 y_limit
        
        # 强制 Y 轴只显示整数刻度
        from matplotlib.ticker import MaxNLocator
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        plt.legend(loc='upper right')
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        
        output_filename = os.path.splitext(video_file)[0] + "_histogram.png"
        output_path = os.path.join(output_folder, output_filename)
        plt.savefig(output_path)
        plt.close() # 关闭图形释放内存
        
        print(f"  Saved histogram to {output_path}")

    print("\nBatch processing complete!")
    print(f"All histograms saved to: {output_folder}")

if __name__ == "__main__":
    main()
