"""
spotify.py: Spotify interface using the verified spotipy library
"""
__author__ = "Cody Deeran"
__copyright__ = "Copyright 2023, codemanbot"
__license__ = "BSD 3-Clause License"
__version__ = "1.0"
__contact__ = {
    "Twitch": "https://twitch.tv/therealcodeman",
    "Youtube": "https://youtube.com/therealcodeman",
    "Twitter": "https://twitter.com/therealcodeman_",
    "Discord": "https://discord.gg/BW34FuYfnK",
    "Email": "dev@codydeeran.com",
}

import asyncio
import json
import shutil
from typing import Any
from enum import Enum
from datetime import datetime
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


class SpotifyReturnCode(Enum):
    """
    Enums for error handling

    Args:
        Enum (_type_): extends Enum type
    """

    SUCCESS = 0
    FAILED = 1
    REQUEST_IS_NOT_A_TRACK = 2
    REQUEST_ALREADY_IN_QUEUE = 3
    FAILED_TO_ESTABLISH_CONNECTION = 4
    FAILED_TO_ADD_TO_QUEUE = 5
    FAILED_TO_BEGIN_PLAYBACK = 6
    NO_CURRENT_PLAYBACK = 7


class SpotifyClient:
    """
    Spotify interface using the verified spotipy library
    """

    def __init__(
        self,
        device_name: str,
        client_id: str,
        client_secret: str,
        redirect: str,
        logging_path: str,
        player_overlay_path: str,
    ):
        self._scope: str = "user-read-playback-state,user-modify-playback-state"
        self._credentials: SpotifyOAuth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect,
            scope=self._scope,
            open_browser=True,
        )
        self.spotify: Spotify = Spotify(client_credentials_manager=self._credentials)
        self._device_name: str = device_name
        self._device_id: int = -1
        self._local_queue: list = []
        self.logging_path: str = logging_path
        self.session_log: str = (
            f"spotify_session_{datetime.now().strftime('%d-%m-%y-%H-%M-%S')}.log"
        )
        self._previous_track_id: str = ""
        self.album_artwork = f"{player_overlay_path}/album_artwork.png"
        self.artist = f"{player_overlay_path}/song_artist.txt"
        self.song_title = f"{player_overlay_path}/song_title.txt"
        self._establish_connection()

    def _find_device_id(self) -> Any:
        """
        Find the device id that was passed in the constructor

        Returns:
            Any: Spotify API indicates the return type is ANY
        """
        device_id = -1
        devices = self.get_devices()
        for device in devices["devices"]:
            if device["name"] == self.get_device_name():
                device_id = device["id"]
        return device_id

    def _set_device_id(self, device_id: int) -> None:
        """
        Set the device id

        Args:
            device_id (int): device id associated with the selected playback device
        """
        self._device_id = device_id

    def _establish_connection(self, max_attempts: int = 3) -> SpotifyReturnCode:
        """
        Establish the connection to spotify

        Args:
            max_attempts (int, optional): Number of retries if connection fails. Defaults to 3.

        Returns:
            SpotifyReturnCode: An enum with the name and value of the error
        """
        current_retries = 1
        device_id = self._find_device_id()

        with open(
            f"{self.logging_path}/{self.session_log}", "a+", encoding="utf-8"
        ) as log:
            while device_id == -1 and current_retries <= max_attempts:
                log.write("Attempting to establish spotify device connection...")
                log.write(f"Retries remaining: {(max_attempts - current_retries)}")
                device_id = self._find_device_id()

            if device_id != -1:
                self._set_device_id(device_id)
                log.write(
                    f"Established connection to device id: {self.get_device_id()}"
                )
                return SpotifyReturnCode.SUCCESS
            else:
                log.write(
                    "Error! Could not establish connection to "
                    f"device named: {self.get_device_name()}"
                )
                return SpotifyReturnCode.FAILED_TO_ESTABLISH_CONNECTION

    def get_devices(self) -> json:
        """
        Get the eligible playback devices associated with the spotify account

        Returns:
            json: Json object with the information associated with the playback devices
        """
        return self.spotify.devices()

    def get_device_id(self) -> Any:
        """
        returns the playback device id

        Returns:
            Any: Spotify api indicates this can be of ANY type for some reason
        """
        return self._device_id

    def get_device_name(self) -> str:
        """
        returns the playback device name

        Returns:
            str: the playback device name
        """
        return self._device_name

    def check_queue(self, requested_track: str) -> SpotifyReturnCode:
        """
        check if requested track is already in the queue

        Args:
            requested_track (str): spotify url

        Returns:
            SpotifyReturnCode: An enum with the name and value of the error
        """
        status = self._update_local_queue()

        if status != SpotifyReturnCode.SUCCESS:
            return status

        for track in self._local_queue:
            if str(track["url"]) == requested_track:
                return SpotifyReturnCode.REQUEST_ALREADY_IN_QUEUE

        return SpotifyReturnCode.SUCCESS

    def get_queued_songs(self) -> dict:
        """
        Get the top 3 queued songs for the users

        Returns:
            dict:
                Key - response: Value - String of top 3 songs to send to user
                Key - return_code: Value - Spotify Return Code
        """
        try:
            current_queue = self.spotify.queue()

            track_counter = 0

            queued_songs = ""

            for song in current_queue["queue"]:
                track_counter += 1
                queued_songs += f"{track_counter}. {song['name']} by {', '.join([artist['name'] for artist in song['artists']])}"

                if track_counter < 3:
                    queued_songs += " | "

                if track_counter == 3:
                    break

            return {"response": queued_songs, "return_code": SpotifyReturnCode.SUCCESS}
        except Exception as error:
            print(error)
            return {"response": "", "return_code": SpotifyReturnCode.FAILED}

    def _update_local_queue(self) -> SpotifyReturnCode:

        try:
            spotify_queue = self.spotify.queue()

            # Get the current song playing so users don't request
            # a song already being played
            currently_playing = spotify_queue["currently_playing"]
            current_track = {
                "title": currently_playing["name"],
                "artists": [artist["name"] for artist in currently_playing["artists"]],
                "url": currently_playing["external_urls"]["spotify"],
                "uri": currently_playing["uri"],
            }
            self._local_queue.append(current_track)

            # Get the rest of the queue to ensure duplicates are not in there
            # NOTE: This will only prevent duplicate requests from interaction with the bot.
            # if the owner of the account has duplicate requests or
            # manually adds a duplicate request there is nothing we can do.
            for request in spotify_queue["queue"]:
                queued_track = {
                    "title": request["name"],
                    "artists": [artist["name"] for artist in request["artists"]],
                    "url": request["external_urls"]["spotify"],
                    "uri": request["uri"],
                }

                self._local_queue.append(queued_track)

            return SpotifyReturnCode.SUCCESS
        except Exception as error:
            print(error.with_traceback())
            return SpotifyReturnCode.FAILED

    def is_valid_track(self, requested_track: str) -> SpotifyReturnCode:
        """
        Verify the requested track is actually a song and not an artist profile
        or playlist. This can be accomplished be checking if the spotify url contains
        /track/. This will only be present if request is indeed a track.

        Args:
            requested_track (str): Spotify song URL

        Returns:
            SpotifyReturnCode: An enum with the name and value of the error
        """
        return (
            SpotifyReturnCode.REQUEST_IS_NOT_A_TRACK
            if "/track/" not in requested_track
            else SpotifyReturnCode.SUCCESS
        )

    def request_track(self, requested_track: str) -> SpotifyReturnCode:
        """
        Add the requested track from user to the queue.

        Must past valid checks.

        Args:
            requested_track (str): URL of the requested song

        Returns:
            SpotifyReturnCode: An enum with the name and value of the error
        """
        valid_track = self.is_valid_track(requested_track)

        if valid_track != SpotifyReturnCode.SUCCESS:
            return valid_track

        # Spotify queue removes the ?si=*
        status = self.check_queue(requested_track.split("?")[0])

        if status != SpotifyReturnCode.SUCCESS:
            return status

        if self.spotify.currently_playing():
            try:
                self.spotify.add_to_queue(uri=requested_track)
                return SpotifyReturnCode.SUCCESS
            except Exception as error:
                with open(
                    f"{self.logging_path}/{self.session_log}", "a+", encoding="utf-8"
                ) as log:
                    log.write(error.with_traceback())
                return SpotifyReturnCode.FAILED_TO_ADD_TO_QUEUE
        else:
            try:
                self.spotify.start_playback(
                    uris=[requested_track], device_id=self.get_device_id()
                )
            except Exception as error:
                with open(
                    f"{self.logging_path}/{self.session_log}", "a+", encoding="utf-8"
                ) as log:
                    log.write(error.with_traceback())
                return SpotifyReturnCode.FAILED_TO_BEGIN_PLAYBACK

    def get_now_playing(self):
        """
        Get and return the current song playing in the format
        of Track by Artists - Spotify Link

        Returns:
            dictionary:
                response: now playing information or error information
                return_code: SUCCESS or NO_CURRENT_PLAYBACK
        """
        if self.spotify.currently_playing():

            response = self.spotify.current_playback()
            track = response["item"]["name"]
            artists = [artist["name"] for artist in response["item"]["artists"]]
            url = response["item"]["external_urls"]["spotify"]
            now_playing = f"{track} by {' | '.join(artists)} - Link: {url}"

            return {"response": now_playing, "return_code": SpotifyReturnCode.SUCCESS}

        return {
            "response": "Failed to get playback. Verify Spotify is up and running.",
            "return_code": SpotifyReturnCode.NO_CURRENT_PLAYBACK,
        }

    async def update_spotify_stream_player(self, interval: int):
        """
        Update the now playing overlay on the Twitch Stream
        """
        while True:
            try:

                # Check that spotify is not paused or down before
                # attempting to grab the queue
                if self.spotify.current_playback() is not None:

                    spotify_queue = self.spotify.queue()

                    # Get the current song playing so users don't request
                    # a song already being played
                    currently_playing = spotify_queue["currently_playing"]
                    current_track = {
                        "artwork_url": currently_playing["album"]["images"][1]["url"],
                        "title": currently_playing["name"],
                        "artists": [
                            artist["name"] for artist in currently_playing["artists"]
                        ],
                        "duration": currently_playing["duration_ms"],
                        "id": currently_playing["id"],
                    }

                    if current_track["id"] != self._previous_track_id:

                        response = requests.get(
                            current_track["artwork_url"], stream=True, timeout=5
                        )

                        if response.status_code == 200:
                            with open(self.album_artwork, "wb") as file:
                                shutil.copyfileobj(response.raw, file)
                        else:
                            print(
                                f"Could not download album artwork for: {current_track['title']}"
                            )

                        # Delete temporary file
                        del response

                        with open(self.song_title, "w", encoding="utf-8") as file:
                            file.write(current_track["title"] + " " * 10)

                        with open(self.artist, "w", encoding="utf-8") as file:
                            file.write(" | ".join(current_track["artists"]))
                            file.write(" " * 5)

                        self._previous_track_id = current_track["id"]

            except Exception as error:
                print(f"{error}")

            await asyncio.sleep(interval)
