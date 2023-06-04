#!/usr/bin/env python
# pyright: reportOptionalMemberAccess=false, reportGeneralTypeIssues=false
import os
import sys
import tempfile
from dotenv import load_dotenv
from spotdl import Spotdl, Song
from spotdl.types.album import Album
from spotdl.types.playlist import Playlist
from PIL import Image
from pathlib import Path
import eyed3
from eyed3.id3.frames import ImageFrame
from dataclasses import dataclass
from urllib.parse import urlparse


def main():
    load_dotenv()
    spotdl = Spotdl(client_id=os.getenv("CLIENT_ID"),
                    client_secret=os.getenv("CLIENT_SECRET"))

    SPOTIFY_URL = sys.argv[1]
    url = urlparse(SPOTIFY_URL)
    url_type = url.path.split('/')[1]

    if url_type == 'playlist':
        Track.set_folder(remove_invalid_char(
            Playlist.get_metadata(SPOTIFY_URL)[0]['name']))
    elif url_type == 'album':
        Track.set_folder(remove_invalid_char(
            Album.get_metadata(SPOTIFY_URL)[0]['name']))
    else:
        Track.set_folder("singles")

    songs = spotdl.search([SPOTIFY_URL])
    tracks = create_tracklist(songs)

    filename_format = Track.folder + '/{title} - {artist}.{output-ext}'

    spotdl.downloader.settings["output"] = filename_format
    spotdl.downloader.settings["bitrate"] = "192k"
    spotdl.downloader.settings["format"] = "mp3"
    spotdl.download_songs(songs)

    covers = get_cover_filenames(songs)
    set_multiple_cover_art(covers, tracks)


def create_tracklist(songs: list[Song]):
    return [Track(song.json['name'], song.json['artist'], song.json['album_name'], song.json['cover_url']) for song in songs]


@dataclass
class Track:
    folder: str = None

    def __init__(
        self,
        title: str = "",
        artist: str = "",
        album: str = "",
        cover: str = None
    ):
        self.title = title
        self.artist = artist
        self.album = album
        self.type = type
        self.cover = cover

    def get_file_path(self):
        file_name = f'{self.title} - {self.artist}.mp3'
        if self.folder is not None:
            return os.path.join(self.folder, remove_invalid_char(file_name))
        return remove_invalid_char(file_name)

    def get_file_name(self):
        file_name = f'{self.title} - {self.artist}.mp3'
        return remove_invalid_char(file_name)

    def set_cover_art(self, tmp_directory: str):
        cover_file_name = f'img-{remove_invalid_char(self.album).lower()}.jpeg'
        audiofile = eyed3.load(self.get_file_path())
        audiofile.tag.images.remove("Cover")
        audiofile.tag.artist = self.artist
        audiofile.tag.images.set(ImageFrame.FRONT_COVER, open(
            os.path.join(tmp_directory, cover_file_name), 'rb').read(), 'image/jpeg')
        audiofile.tag.save(version=eyed3.id3.ID3_V2_3)

    @classmethod
    def set_folder(cls, name):
        cls.folder = os.path.join(Path.home(), "Music", name)


def set_multiple_cover_art(covers, tracks: list[Track]):

    with tempfile.TemporaryDirectory() as td:
        # download all covers
        for cover in covers:
            os.system(
                f'aria2c {cover["cover_url"]} --dir={td} --out="{cover["file_name"]}" --disable-ipv6')
            image = Image.open(os.path.join(td, cover['file_name']))
            res_image = image.resize((256, 256))
            res_image.save(os.path.join(
                td, cover["file_name"]), 'JPEG', quality=60)

        for track in tracks:
            track.set_cover_art(td)


def get_cover_filenames(songs):
    cover_filenames = []
    album_list = []
    for idx, song in enumerate(songs):
        song_json = song.json
        album_name = remove_invalid_char(song_json['album_name'])
        file_name = f'img-{album_name.lower()}.jpeg'
        cover_url = song_json['cover_url']

        if album_name not in album_list:
            cover_filenames.append(
                {'id': idx, 'album': album_name, 'file_name': file_name, 'cover_url': cover_url})
            album_list.append(album_name)

    return cover_filenames


def remove_invalid_char(str):
    # Bad character list
    str = str.replace('"', "'")
    bad_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    return ''.join(c for c in str if not c in bad_chars)


if __name__ == '__main__':
    main()
