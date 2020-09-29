import os
import requests
import base64
import datetime
from functools import wraps


class SpotifyClient(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    _token_url = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

        try:
            self.access_token = self.get_access_token()
            if self.access_token is None:
                raise Exception("Failed Access Token Request")
        except Exception as e:
            print(e)

    class Decorators():

        @staticmethod
        def refreshToken(decorated):
            @wraps(decorated)
            def wrapper(api, *args, **kwargs):
                now = datetime.datetime.now()
                if now > api.access_token_expiration_time:
                    api.get_access_token()
                return decorated(api, *args, **kwargs)

            return wrapper

    @Decorators.refreshToken
    def make_get_request(self, url, headers='bearer', method="GET", params=None):
        if headers=='bearer':
            headers = self.get_bearer_token_headers()
        error_url = "{} : {}"
        try:
            r = requests.request(method=method, url=url, headers=headers, params=params)
        except requests.exceptions.HTTPError as e:
            print(error_url.format(url, e))
            return None
        except requests.exceptions.ConnectionError as e:
            print(error_url.format(url, e))
            return None
        except requests.exceptions.Timeout as e:
            print(error_url.format(url, e))
            return None
        except requests.exceptions.RequestException as e:
            print(error_url.format(url, e))
            return None
        return r


    def get_auth_token_headers(self):
        client_credentials_b64 = self.get_client_credentials()
        return {"Authorization": f"Basic {client_credentials_b64.decode()}"}

    def get_client_credentials(self):
        """returns base64 encoded string"""
        if self.client_id is None or self.client_secret is None:
            raise Exception("you must set client_id and client_secret")
        client_credentials = f"{self.client_id}:{self.client_secret}"
        client_credentials_b64 = base64.b64encode(client_credentials.encode())
        return client_credentials_b64

    def get_token_data(self):
        return {"grant_type": "client_credentials"}

    def get_access_token(self, method='POST'):
        try:
            url = self._token_url
            data = self.get_token_data()
            headers = self.get_auth_token_headers()
            r = requests.request(method=method, url=url, data=data, headers=headers)
            r.raise_for_status()
        except Exception as e:
            print(e)
            return None
        else:
            token_data = r.json()
            now = datetime.datetime.now()
            access_token = token_data['access_token']
            expires_in = token_data['expires_in']
            self.access_token_expiration_time = now + datetime.timedelta(seconds=expires_in)
            return access_token

    def get_bearer_token_headers(self):
        if self.access_token is None:
            raise Exception("Must first get access token using perform_auth() method")

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        return headers


    def search(self, **params):
        """
        perform sarch query on spotify api
        :param data: dict
        type Required.
            type of spotify object album, artist, single, song, playlist, etc
        q	Required.
            Search query keywords and optional field filters and operators.
            For example:
            q=roadhouse%20blues.
            type	Required.
            A comma-separated list of item types to search across.
            Valid types are: album , artist, playlist, track, show and episode.
            Search results include hits from all the specified item types.
            For example: q=name:abacab&type=album,track returns both albums and tracks
            with “abacab” included in their name.
        market	Optional.
            An ISO 3166-1 alpha-2 country code or the string from_token.
            If a country code is specified, only artists, albums, and tracks with content
            that is playable in that market is returned.
            Note:
            - Playlist results are not affected by the market parameter.
            - If market is set to from_token, and a valid access token is specified in
            the request header, only content playable in the country associated with the
            user account, is returned.
            - Users can view the country that is associated with their account in the account settings.
            A user must grant access to the user-read-private scope
            prior to when the access token is issued.
        limit	Optional.
            Maximum number of results to return.
        Default: 20
        Minimum: 1
        Maximum: 50
            Note: The limit is applied within each type, not on the total response.
            For example, if the limit value is 3 and the type is artist,album,
            the response contains 3 artists and 3 albums.
        offset	Optional.
            The index of the first result to return.
        Default: 0 (the first result).
        Maximum offset (including limit): 2,000.
            Use with limit to get the next page of search results.
        include_external	Optional.
        Possible values: audio
            If include_external=audio is specified the response will include any relevant
            audio content that is hosted externally.
        By default external content is filtered out from responses.
        :return:

        On success:
            In the response header the HTTP status code is 200 OK.
            For each type provided in the type parameter, the response body contains an
            array of artist objects / simplified album objects / track objects /                   simplified show objects / simplified episode objects wrapped in a paging               object in JSON.
        On error:
            The header status code is an error code.
            The response body contains an error object.
        """
        search_url = "https://api.spotify.com/v1/search"
        r = self.make_get_request(url=search_url, params=params)
        search_data = r.json()
        return search_data


    def search_artist(self, id):
        """
        searches artist by id
        :param id: default None. If None returns a list of artists
            if id is not None uses id to returns artist meta information
            artist spotify id. ex: Kanye West id = 5K4W6rqBFWDnAN6FQUkS6x
        :param meta: default None. If None returns artist information
            meta="albums", returns artist's albums
            meta="top-tracks", returns artist's top-tracks
            meta="related-artists", returns artist's related artists
        :param country: default None. Needed if meta = "top-tracks"
        :return:
            spotify object for desired query
        """
        artist_url = f"https://api.spotify.com/v1/{id}"
        bearer_token_headers = self.get_bearer_token_headers()
        method = "GET"
        r = self.make_get_request(url=artist_url, method=method, headers=bearer_token_headers)
        return r.json()

    def search_artists(self, ids):
        """
        search multiple artists by their ids
        :param ids: list of artist ids
        :return:
        """
        ids = ",".join(ids)
        params = {"ids":ids}
        search_artists_url = "https://api.spotify.com/v1/artists"
        r = self.make_get_request(url=search_artists_url, params=params)
        return r.json()

    def _search_artist_endpoint(self, id, endpoint, params):
        artist_url = f"https://api.spotify.com/v1/{id}/{endpoint}"
        r = self.make_get_request(url=artist_url, params=params)
        return r.json()

    def search_artist_albums(self, id, **params):
        endpoint = "albums"
        r = self._search_artist_endpoint(id=id, endpoint=endpoint, params=params)
        return r.json()

    def search_arist_top_tracks(self, id, **params):
        endpoint = "top-tracks"
        r = self._search_artist_endpoint(id=id, endpoint=endpoint, params=params)
        return r.json()

    def search_artist_related_artists(self, id, **params):
        endpoint = "related-artists"
        r = self._search_artist_endpoint(id=id, endpoint=endpoint, params=params)
        return r.json()

    def search_albums(self, id):
        pass

    def search_album(self):
        pass

    def search_album_track(self, id):
        pass

