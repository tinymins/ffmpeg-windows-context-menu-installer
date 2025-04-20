import os
import re
import subprocess
from datetime import datetime, timedelta

def extract_datetime_from_filename(filename):
    match = re.match(r"(\d{14})_.*\.MP4", filename)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    return None

def group_videos_by_time(videos, max_time_difference=120):
    videos.sort()
    grouped_videos = []
    current_group = []

    for i, video in enumerate(videos):
        if i == 0:
            current_group.append(video)
            continue

        current_time = extract_datetime_from_filename(video)
        previous_time = extract_datetime_from_filename(videos[i - 1])

        if current_time and previous_time:
            if (current_time - previous_time).total_seconds() <= max_time_difference:
                current_group.append(video)
            else:
                grouped_videos.append(current_group)
                current_group = [video]

    if current_group:
        grouped_videos.append(current_group)

    return grouped_videos

def check_combined_file_exists(file):
    combined_folder = os.path.join(os.getcwd(), 'combined')
    if not os.path.exists(combined_folder):
        os.makedirs(combined_folder)
    combined_filename = os.path.join(combined_folder, os.path.basename(file))
    return os.path.exists(combined_filename)

def merge_videos(video_group, combined_file):
    with open("concat_list.txt", "w") as f:
        for video in video_group:
            f.write(f"file '{video}'\n")

    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt',
        '-c', 'copy', combined_file
    ]

    os.system("pause")
    subprocess.run(command, check=True)
    os.remove("concat_list.txt")

def process_videos_in_folder(folder_path):
    videos = [f for f in os.listdir(folder_path) if f.endswith('.MP4')]
    full_video_paths = [os.path.join(folder_path, v) for v in videos]

    grouped_videos = group_videos_by_time(full_video_paths)

    for group in grouped_videos:
        first_video_datetime = extract_datetime_from_filename(os.path.basename(group[0]))
        combined_file_name = f"{first_video_datetime.strftime('%Y%m%d%H%M%S')}.MP4"
        combined_file_path = os.path.join(os.getcwd(), 'combined', combined_file_name)

        if not check_combined_file_exists(combined_file_path):
            merge_videos(group, combined_file_path)
        else:
            print(f"Combined file already exists for group starting with {combined_file_name}, skipping...")

if __name__ == "__main__":
    folder_path = input("Please enter the video folder path: ")
    process_videos_in_folder(folder_path)
