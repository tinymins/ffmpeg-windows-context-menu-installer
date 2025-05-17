import os
import re
import shutil
import subprocess
from datetime import datetime

def parse_video_filename(filename):
    # 原有格式：20250419195801_000785AC.MP4
    match = re.match(r"(\d{14})_(.+\.MP4)", filename, re.IGNORECASE)
    if match:
        datetime_str = match.group(1)
        rest_of_filename = match.group(2)
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S"), rest_of_filename, 120

    # 新格式：NO20200101-001521-002110B.mp4
    match = re.match(r"[A-Za-z]+(\d{8})-(\d{6})-(\d+[A-Za-z]+\.MP4)", filename, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        rest_of_filename = match.group(3)
        datetime_str = date_str + time_str
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S"), rest_of_filename, 200

    return None, None, None

def extract_camera_id(filename):
    # 原有格式：从 "20250419195801_000785AC.MP4" 提取 "AC"
    match = re.match(r"\d{14}_\d+([A-Z]+)\.MP4", filename, re.IGNORECASE)
    if match:
        return match.group(1)

    # 新格式：从 "NO20200101-001521-002110B.mp4" 提取 "B"
    match = re.match(r"[A-Za-z]+\d{8}-\d{6}-\d+([A-Za-z]+)\.MP4", filename, re.IGNORECASE)
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

def group_videos_by_time(video_camera_groups):
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

            current_time, _, max_time_difference = parse_video_filename(os.path.basename(video))
            previous_time, _, _ = parse_video_filename(os.path.basename(video_series[i - 1]))

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

def create_combined_filename(first_video, last_video):
    """创建合并后的文件名，格式为：第一个视频时间_最后一个视频时间_其余部分.MP4"""
    first_basename = os.path.basename(first_video)
    last_basename = os.path.basename(last_video)

    first_datetime, first_rest, _ = parse_video_filename(first_basename)
    last_datetime, _, _ = parse_video_filename(last_basename)

    if not first_datetime or not last_datetime:
        return first_basename  # 如果无法提取时间，返回原始文件名

    # 将datetime对象转换为字符串格式
    first_timestamp = first_datetime.strftime("%Y%m%d%H%M%S")
    last_timestamp = last_datetime.strftime("%Y%m%d%H%M%S")

    return f"{first_timestamp}_{last_timestamp}_{first_rest}"

def merge_videos(video_group, combined_file):
    # 获取最后一个视频文件的时间属性
    last_video = video_group[-1]
    last_video_stats = os.stat(last_video)
    last_access_time = last_video_stats.st_atime
    last_mod_time = last_video_stats.st_mtime

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

    # 设置合并后文件的时间属性为最后一个视频文件的时间属性
    os.utime(combined_file, (last_access_time, last_mod_time))
    print("Merge complete. File timestamps set to match the last video segment.")

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

            # 获取该组的第一个视频文件和最后一个视频文件
            first_video = group[0]
            last_video = group[-1]

            # 获取原文件的相对路径
            relative_dir = os.path.dirname(os.path.relpath(first_video, src_folder))
            target_folder = os.path.join(target_folder_base, relative_dir)

            # 创建目标文件夹
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            # 构建输出文件名 - 使用新的命名格式
            combined_file_name = create_combined_filename(first_video, last_video)
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
            target_file_path = os.path.join(target_folder_base, relative_path)
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
    target_folder_base = os.path.join(os.path.dirname(src_folder), f'{os.path.basename(src_folder)}_Combined')
    print(f"Output files will be placed in: {target_folder_base}")
    process_videos_in_folder(src_folder, target_folder_base)
    os.system('pause')
