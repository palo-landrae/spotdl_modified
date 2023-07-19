import os
import eyeD3


def set_year(mp3_file):
    audio = eyeD3.Mp3AudioFile(mp3_file)
    tag = audio.getTag()
    if tag and tag.getYear():
        print(tag.getYear())
        return True
    return False


def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp3"):
                mp3_file = os.path.join(root, file)
                status = set_year(mp3_file)
                print(f"File: {mp3_file} | Success: {status}")


# Change the directory path to the desired directory
directory_path = "/home/landrae/Music"
process_directory(directory_path)
