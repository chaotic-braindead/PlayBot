import requests
import base64


class SpotifyAPI:
    def __init__(self, access_token):
        self.access_token = access_token

    @staticmethod
    def extract_access_token(CLIENT_ID, CLIENT_SECRET):
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        b64_creds = base64.b64encode(credentials.encode())
        token_data = {"grant_type": "client_credentials"}
        header = {"Authorization": f"Basic {b64_creds.decode()}"}
        url = "https://accounts.spotify.com/api/token"
        r = requests.post(url=url, headers=header, data=token_data)

        if r.status_code in range(200, 299):
            token_response = r.json()
            access_token = token_response["access_token"]

            return access_token

        while not access_token:
            access_token = SpotifyAPI.extract_access_token(CLIENT_ID, CLIENT_SECRET)
            return access_token

    def get(self, track_id):
        if not track_id.startswith("https://api.spotify.com/v1/tracks/"):
            track_id = f"https://api.spotify.com/v1/tracks/{track_id}"
        header = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(track_id, headers=header)
        if r.status_code not in range(200, 299):
            return None
        track_data = r.json()
        track_artists = ", ".join(
            track_data["artists"][i]["name"] for i in range(len(track_data["artists"]))
        )
        track_title = track_data["name"]
        return f"{track_artists} - {track_title}"


if __name__ == "__main__":
    import os

    CLIENT_ID = os.environ.get("PLAYBOT_SPOTI_ID")
    CLIENT_SECRET = os.environ.get("PLAYBOT_SPOTI_SECRET")

    access_token = SpotifyAPI.extract_access_token(CLIENT_ID, CLIENT_SECRET)
    spotify = SpotifyAPI(access_token)

    print(spotify.get("6QLNcOI6YCqdLAS6GLWXMj"))
