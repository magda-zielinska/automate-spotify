import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl
from logins import spotify_user_id

class CreateSpotifyPlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.all_songs = {}

    def youtube_login(self):

        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        api_service_name = 'youtube'
        api_version = 'v3'
        client_secrets_file = 'client_secret.json'

        scopes = ['https.//www.googleapis.com.auth/youtube.readonly']
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file,
                                                                                   scopes)
        credentials = flow.run_console()

        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_videos(self):
        requests = self.youtube_client.videos().list(
            part='snippet,contentDetails,statistics',
            myRating = 'like'
        )
        response = requests.execute()

        for item in response['items']:
            video_title = item['snippet']['title']
            youtube_url = 'https://www.youtube.com/watch?v={}'.format(item['id'])

            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url,download=False)
            song_name = video['track']
            artist = video['artist']

            self.all_songs[video_title] = {
                'youtube_url': youtube_url,
                'song_name': song_name,
                'artist': artist,

                'spotify_uri' : self.get_spotify_uri(song_name, artist)
            }

    def create_spotify_playlist(self):
        request_body = json.dumps({
            'name': 'Songs Found On Youtube',
            'description':'Songs liked on Youtube',
            'public': True
        })

        query = 'https://api.spotify.com/v1/users/{}/playlists'.format(self.user_id)
        response = requests.post(
             query,
            data=request_body,
            headers={
                'Content-Type':'application/json',
                'Autorization':'Bearer {}'.format(self.spotify_token)
            }
        )
        response_json = response.json()

        # playlist id
        return response_json('id')

    def get_spotify_uri(self, song_name, artist):
        query = 'https://api.spotify.com/v1/search?query=track%3A{}+artist%A{}&type=track&offset=0&limit=20'.format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                'Content-Type': 'application/json',
                'Autorization': 'Bearer {}'.format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json['tracks']['items']

        uri = songs[0]['uri']
        return uri

    def add_song_to_playlist(self):
        self.get_liked_videos()

        uris = []
        for song, info in self.all_songs.items():
            uris.append(info['spotify_uri'])

        playlist_id = self.create_spotify_playlist()

        request_data = json.dumps(uris)

        query = 'https://api.spotify.com/v1/playlist/{}/tracks'.format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                'Content-Type': 'application/json',
                'Autorization': 'Bearer {}'.format(self.spotify_token)
            }
        )
        response_json = response.json()
        return response_json
