import os
import re
import shutil
import subprocess
from datetime import datetime

def extract_datetime_from_filename(filename):
    match = re.match(r"(\d{14})_.*\.MP4", filename)
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

def check_combined_file_exists(target_folder, file_name):
    combined_file_path = os.path.join(target_folder, file_name)
    return os.path.exists(combined_file_path)

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
    all_mp4_files = []

    # 首先收集所有MP4文件
    for dirpath, _, files in os.walk(src_folder):
        mp4_files = [os.path.join(dirpath, f) for f in files if f.endswith('.MP4')]
        all_mp4_files.extend(mp4_files)

    print(f"Found {len(all_mp4_files)} MP4 files in total.")

    # 按照摄像机ID进行初始分组
    camera_groups = group_videos_by_camera(all_mp4_files)
    print(f"Files divided into {len(camera_groups)} different camera groups.")

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
        first_video_datetime = extract_datetime_from_filename(first_video_basename)

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

        if not check_combined_file_exists(target_folder, combined_file_name):
            merge_videos(group, combined_file_path)
        else:
            print(f"Combined file already exists for group starting with {combined_file_name}, skipping...")

    print(f"\nProcessing completed. {processed_groups} groups processed.")

if __name__ == "__main__":
    src_folder = input("Please enter the video folder path: ")
    target_folder_base = os.getcwd()  # Change this if you want a different base directory for combined files
    process_videos_in_folder(src_folder, target_folder_base)
