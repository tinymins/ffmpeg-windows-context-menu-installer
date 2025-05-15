import os
import re
import shutil
import subprocess
from datetime import datetime

def extract_datetime_from_filename(filename):
    match = re.match(r"(\d{14})_.*\.MP4", filename, re.IGNORECASE)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    return None

def extract_camera_id(filename):
    # 提取文件名中的摄像机ID/通道标识，例如从 "20250419195801_000785AC.MP4" 提取 "AC"
    match = re.match(r"\d{14}_\d+([A-Z]+)\.MP4", filename, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def group_videos_by_camera(videos):
    # 按照摄像机ID进行初始分组
    camera_groups = {}
    for video in videos:
        basename = os.path.basename(video)
        camera_id = extract_camera_id(basename)
        if camera_id not in camera_groups:
            camera_groups[camera_id] = []
        camera_groups[camera_id].append(video)

    # 返回所有分组
    return list(camera_groups.values())

def group_videos_by_time(video_camera_groups, max_time_difference=120):
    final_groups = []

    # 对每个摄像机组内的视频按时间进行进一步分组
    for video_series in video_camera_groups:
        video_series.sort(key=lambda x: os.path.basename(x))
        time_grouped = []
        current_group = []

        for i, video in enumerate(video_series):
            if i == 0:
                current_group.append(video)
                continue

            current_time = extract_datetime_from_filename(os.path.basename(video))
            previous_time = extract_datetime_from_filename(os.path.basename(video_series[i - 1]))

            if current_time and previous_time:
                time_diff = (current_time - previous_time).total_seconds()
                if time_diff <= max_time_difference:
                    current_group.append(video)
                else:
                    time_grouped.append(current_group)
                    current_group = [video]

        if current_group:
            time_grouped.append(current_group)

        final_groups.extend(time_grouped)

    return final_groups

def check_file_exists(file_path):
    return os.path.exists(file_path)

def merge_videos(video_group, combined_file):
    if len(video_group) == 1:
        # Copy the single file directly
        print(f"Copying single file: {video_group[0]} to {combined_file}")
        shutil.copy2(video_group[0], combined_file)
        return

    print(f"Merging {len(video_group)} files into: {combined_file}")
    print(f"Files to merge: {[os.path.basename(v) for v in video_group]}")

    with open("concat_list.txt", "w") as f:
        for video in video_group:
            f.write(f"file '{video}'\n")

    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt',
        '-c', 'copy', combined_file
    ]

    subprocess.run(command, check=True)
    os.remove("concat_list.txt")
    print("Merge complete.")

def process_videos_in_folder(src_folder, target_folder_base):
    mp4_files = []
    other_files = []

    # 收集所有文件
    print("Scanning for files...")
    for dirpath, _, files in os.walk(src_folder):
        for filename in files:
            full_path = os.path.join(dirpath, filename)
            if filename.lower().endswith('.mp4'):
                mp4_files.append(full_path)
            else:
                # 确保不是文件夹（虽然在files列表中不会有文件夹，为了代码健壮性）
                if os.path.isfile(full_path):
                    other_files.append(full_path)

    print(f"Found {len(mp4_files)} MP4 files and {len(other_files)} other files.")

    # 处理MP4文件
    if mp4_files:
        # 按照摄像机ID进行初始分组
        camera_groups = group_videos_by_camera(mp4_files)
        print(f"MP4 files divided into {len(camera_groups)} different camera groups.")

        # 进一步按照时间关系进行分组
        grouped_videos = group_videos_by_time(camera_groups)
        total_groups = len(grouped_videos)
        print(f"Total video groups to process: {total_groups}")

        processed_groups = 0

        # 处理每个视频组
        for group in grouped_videos:
            processed_groups += 1

            # 获取该组的第一个视频文件
            first_video = group[0]
            first_video_basename = os.path.basename(first_video)

            # 获取原文件的相对路径
            relative_dir = os.path.dirname(os.path.relpath(first_video, src_folder))
            target_folder = os.path.join(target_folder_base, 'combined', relative_dir)

            # 创建目标文件夹
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            # 构建输出文件名 - 使用完整的原始文件名
            combined_file_name = os.path.basename(first_video)
            combined_file_path = os.path.join(target_folder, combined_file_name)

            print(f"\nProcessing group {processed_groups}/{total_groups}: {combined_file_name}")
            print(f"Group contains {len(group)} files")

            if not check_file_exists(combined_file_path):
                merge_videos(group, combined_file_path)
            else:
                print(f"Combined file already exists: {combined_file_path}, skipping...")

        print(f"\nMP4 processing completed. {processed_groups} groups processed.")

    # 处理其他类型文件
    if other_files:
        print("\nProcessing other file types...")
        copied_count = 0
        skipped_count = 0

        for file_path in other_files:
            relative_path = os.path.relpath(file_path, src_folder)
            target_file_path = os.path.join(target_folder_base, 'combined', relative_path)
            target_dir = os.path.dirname(target_file_path)

            # 确保目标目录存在
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            if not check_file_exists(target_file_path):
                print(f"Copying: {relative_path}")
                shutil.copy2(file_path, target_file_path)
                copied_count += 1
            else:
                print(f"File already exists: {relative_path}, skipping...")
                skipped_count += 1

        print(f"\nOther files processing completed. {copied_count} files copied, {skipped_count} files skipped.")

    print("\nAll processing completed successfully!")

if __name__ == "__main__":
    src_folder = input("Please enter the source folder path: ")
    target_folder_base = os.getcwd()  # 默认使用当前工作目录作为目标文件夹的基路径
    print(f"Output files will be placed in: {os.path.join(target_folder_base, 'combined')}")
    process_videos_in_folder(src_folder, target_folder_base)
