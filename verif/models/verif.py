"""
Verification parent class
"""
import datetime
import xarray as xr
from verif.obs import ddb, utils, obsAPI


class VerifModelStation():
    """ Generic Class for Model verification for one station against an observation source.

    Args:
        station (str): WMO station id.
        dt_start (datetime.datetime): The start model basetime
        dt_end (datetime.datetime): The end model basetime
        fcast_window (int): number of days to include in the obs windows after dt_end
        obs_source (str): obs data source ('DDB_obs', 'API_obs')
        model (str): model to verify (need to be referenced in the Yaml)
        model_vars (list): list of model variables we want to verify
        freq (str): frequency requested (None: all points, 'hourly', '10min' )  
    """

    def __init__(self,
                 station_id,
                 dt_start,
                 dt_end,
                 obs_source,
                 model,
                 model_vars,
                 fcast_window=0,
                 freq=None,
                 api_key=None
                 ):
        self.station_id = station_id
        self.dt_start = dt_start
        self.dt_end = dt_end
        self.obs_source = obs_source
        self.model = model
        self.model_vars = model_vars
        self.fcast_window = fcast_window
        self.freq = freq
        self.api_key = api_key
        self.obs_ds = None


    def query_obs(self):
        """ Query the obs source - all data points
        Args:
            obs_source (str): obs data source ('DDB', 'API')
            model_vars (list): list of model vararibles we want to verify
        """
        obs_vars = utils.load_obs_vars()

        self.obs_ds = xr.Dataset()

        if self.obs_source=='DDB_obs':
            try:
                obs_id = utils.get_obs_id(self.station_id)
            except KeyError:
                print('Station not in iceobs_stations for DDB! Please use another obs source')
                return
            obs_all = ddb.get_obs_all(f'{obs_id}_nzaws',
                                      self.dt_start,
                                      self.dt_end + datetime.timedelta(days=self.fcast_window),
                                      table_recent = True)
            for model_var in self.model_vars:
                # get the obs var to retrieve
                try:
                    obs_var = list(obs_vars[self.model][model_var][self.obs_source].keys())[0]
                except KeyError:
                    print(f'{model_var}/{self.model}/{self.obs_source} not in the obs_var list!')
                    return
                obs_var_serie = ddb.extract_obs_data(obs_all, obs_var, self.freq)

                # convert to the model unit
                obs_var_serie = (obs_var_serie * obs_vars[self.model][model_var][self.obs_source][obs_var]['conv'][0]
                                + obs_vars[self.model][model_var][self.obs_source][obs_var]['conv'][1]
                                )
                # add metedata
                obs_var_serie.attrs['observation source'] = f'{self.obs_source} - converted units'
                obs_var_serie.attrs['observation var'] = obs_var
                obs_var_serie.attrs['unit'] = obs_vars[self.model][model_var]['unit']

                self.obs_ds[f'{model_var}_obs'] = obs_var_serie

        elif self.obs_source=='API_obs':
            obs_api = obsAPI.RequestAPI(station_id=self.station_id, apikey=self.api_key)
            obs_all = obs_api.query_range(self.dt_start,
                                          self.dt_end + datetime.timedelta(days=self.fcast_window))
        
            for model_var in self.model_vars:
                # get the obs var to retrieve
                try:
                    obs_var = list(obs_vars[self.model][model_var][self.obs_source].keys())[0]
                except KeyError:
                    print(f'{model_var}/{self.model}/{self.obs_source} not in the obs_var list!')
                    return
                obs_var_serie = obs_api.extract_obs_data(obs_var, self.freq)

                # convert to the model unit
                obs_var_serie = (obs_var_serie * obs_vars[self.model][model_var][self.obs_source][obs_var]['conv'][0]
                                + obs_vars[self.model][model_var][self.obs_source][obs_var]['conv'][1]
                                )
                # add metedata
                obs_var_serie.attrs['observation source'] = f'{self.obs_source} - converted units'
                obs_var_serie.attrs['observation var'] = obs_var
                obs_var_serie.attrs['unit'] = obs_vars[self.model][model_var]['unit']

                self.obs_ds[f'{model_var}_obs'] = obs_var_serie

        return self.obs_ds