"""
Utility functions for observation datasources querying and cleaning
"""

import pkg_resources
import yaml
import datetime
import json

from verif.obs import ddb

def load_obs_vars():
    ''' Loads the obs/models var catalogue
    '''
    file = pkg_resources.resource_filename('verif', 'data/obs_vars.yaml')
    with open(file, 'r') as f:
        obs_vars = yaml.safe_load(f)
    return obs_vars


def load_iceobs_stations():
    ''' Loads the iceobs ataion list for obs_id/wmo conversion
    '''
    file = pkg_resources.resource_filename('verif', 'data/iceobs_stations.json')
    with open(file, 'r') as f:
        obs_vars = json.load(f)
    return obs_vars


def get_obs_serie(wmo_code: str,
                  model:str,
                  model_var:str,
                  obs_source:str,
                  dt_start: datetime.datetime,
                  dt_end: datetime.datetime,
                  freq=None):
    """
    Create an obs time serie for a model to verify and for a given station 
    Args:
        wmo_code (str):wmo code of the station
        model (str): model to apply the obs data to ('ePD', 'DLITE', 'WRF', 'MLPP'....)
        model_var (str): model ouput var to verify
        obs_source (str): obs data source ('DDB_obs', 'API_obs')
        dt_start: datetime.datetime, 
        dt_end: datetime.datetime
        freq (str): frequency requested (None: all points, 'hourly': only hourly (0 minutes) points ) 

    Returns:
        DataArray: xarray DataArray containing the data with metadata of obs var
    """
    obs_vars = load_obs_vars()
    obs_stations = load_iceobs_stations()
    
    # get the obs_id from the wmo code
    try:
        obs_id = obs_stations[wmo_code]['name']
    except KeyError:
        print('Station not in iceobs_stations!')
        return
    
    # get the obs var to retrieve
    try:
        obs_var = list(obs_vars[model][model_var][obs_source].keys())[0]
    except KeyError:
        print('Variable/model/obs_source not in the obs_var list!')
        return
    
    if obs_source=='DDB_obs':
        obs_all = ddb.get_obs_all(f'{obs_id}_nzaws', dt_start, dt_end, table_recent = True)
        obs_var_serie = ddb.extract_obs_data(obs_all, obs_var, freq)

        # convert to the model unit
        obs_var_serie = (obs_var_serie * obs_vars[model][model_var][obs_source][obs_var]['conv'][0]
                           + obs_vars[model][model_var][obs_source][obs_var]['conv'][1]
                           )
        # add metedata
        obs_var_serie.attrs['observation source'] = f'{obs_source} - converted units'
        obs_var_serie.attrs['observation var'] = obs_var
        obs_var_serie.attrs['unit'] = obs_vars[model][model_var]['unit']

    #elif obs_source='API_obs':

    return obs_var_serie
