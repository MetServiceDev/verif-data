import requests
import json
import datetime


api_url = "https://test-api.metservice.com/observations/nz/1-minute/weatherStation/{station_id}"


class RequestAPI:
    """Request observation data from the MetService OneMinuteObs API.

    Args:
        station_id (int): The ID of the weather station.
        apikey (str): The API Key to be used in the request.

    Attributes:
        session (requests.Session): The session to be used for the request.
        base_url (str): The base URL for the API.
        headers (dict): The headers to be used in the request (i.e., API key).

    Methods:
        query_last(n_mins): Query the last n_mins minutes of data.
        query_range(start, end): Query the data between start and end.

    Example:
        >>> from verif.data.obs.obsAPI import RequestAPI
        >>> api = RequestAPI(station_id=93106, apikey="1234567890")
        >>> api.query_last(60)
        >>> api.query_range(datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 2))

    """

    def __init__(self, station_id: int, apikey: str):
        self.session = requests.Session()
        self.base_url = api_url.format(station_id=str(station_id))
        self.headers = {"apikey": apikey}

    def query_last(self, n_mins: int):
        url = self.base_url + f"/last/{n_mins}/minutes?format=cf-json"
        response = self.session.get(url, headers=self.headers)
        return json.loads(response.content)

    def query_range(self, start: datetime.datetime, end: datetime.datetime):
        url = (
            self.base_url
            + f"/range/{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}?format=cf-json"
        )
        response = self.session.get(url, headers=self.headers)
        return json.loads(response.content)
