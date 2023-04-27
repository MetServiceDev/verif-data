import requests
import json
import datetime
import numpy as np
import xarray as xr


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
        extract_obs_data(var_name, freq): Extract the variable at given freq as a Xarray da

    Example:
        >>> from verif.data.obs.obsAPI import RequestAPI
        >>> api = RequestAPI(station_id=93106, apikey="1234567890")
        >>> api.query_last(60)
        >>> api.query_range(datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 2))
        >>> api.extract_obs_data('airtemp_01mnavg', freq='hourly')

    """

    def __init__(self, station_id: int, apikey: str):
        self.session = requests.Session()
        self.base_url = api_url.format(station_id=str(station_id))
        self.headers = {"apikey": apikey}
        self.obs_all=[]
        self.da=None

    def query_last(self, n_mins: int):
        url = self.base_url + f"/last/{n_mins}/minutes?format=json"
        response = self.session.get(url, headers=self.headers)
        self.obs_all = json.loads(response.content)['results']
        return self.obs_all

    def query_range(self, start: datetime.datetime, end: datetime.datetime):
        """ Query a date range
            Multiple queries for request > 1day
        """

        if end-start <= datetime.timedelta(days=1):
            url = (self.base_url +
                   f"/range/{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}?format=json"
                  )
            response = self.session.get(url, headers=self.headers)
            content = json.loads(response.content)
            try:
                self.obs_all = content['results']
            except KeyError:
                pass
        else:
            current = start
            while end-current > datetime.timedelta(days=1):
                current_end = current + datetime.timedelta(days=1)
                url = (self.base_url +
                       f"/range/{current.strftime('%Y-%m-%dT%H:%M:%SZ')}/{current_end.strftime('%Y-%m-%dT%H:%M:%SZ')}?format=json"
                      )
                response = self.session.get(url, headers=self.headers)
                content = json.loads(response.content)
                try:
                    self.obs_all.extend(content['results'])
                except KeyError:
                    pass
                current += datetime.timedelta(days=1)

            url = (self.base_url +
                   f"/range/{current.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}?format=json"
                  )
            response = self.session.get(url, headers=self.headers)
            content = json.loads(response.content)
            try:
                self.obs_all.extend(content['results'])
            except KeyError:
                pass

        return self.obs_all
    
    def extract_obs_data(self, var_name: str, freq: str=None):
        """ Extract obs serie for given var and frequency """
        valid_time = []
        data = []
        for obs in self.obs_all:
            dt = datetime.datetime.fromisoformat(obs["obs_timestamp"][:-1])
            if freq == "hourly":
                if dt.minute == 0:
                    valid_time.append(dt)
                    try:
                        data.append(float(obs[var_name]))
                    except:
                        data.append(np.nan)
            elif freq == "10min":
                if dt.minute % 10 == 0:
                    valid_time.append(dt)
                    try:
                        data.append(float(obs[var_name]))
                    except:
                        data.append(np.nan)
            else:
                valid_time.append(dt)
                try:
                    data.append(float(obs[var_name]))
                except:
                    data.append(np.nan)

        self.da = xr.DataArray(
            data,
            coords={
                "time": valid_time,
            },
            dims=["time"],
            ).drop_duplicates(dim='time').sortby('time')

        return self.da