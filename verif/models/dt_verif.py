"""
Functions for verifying DeepThought ePD/DLITE outputs

"""
import datetime
import numpy as np
from scipy.stats import norm
import pandas as pd
import xarray as xr
import properscoring as ps
from dt_output import get_dt_output

from verif.obs.utils import get_obs_serie
from verif.models.verif import VerifModelStation



def verify_dt_ouput(station, dt_start, dt_end, predictand, dt_kind):
    """Verify probabilistic DeepThought forecast a time period
        Calculate probabilistic metrics for each basetime/prognosis_period:
            - Observation probability and cumulative probabilty (for PIT histogram)
            - Observation negative log likelihood
            - Continuous Rank Probability Score

    Args:
        station (str): WMO station id.
        dt_start (datetime.datetime): The start datetime.
        dt_end (datetime.datetime): The end datetime.
        predictand (str): DeepThought predictand requested (ex 'TTTTT')
        dt_kind (str): either "ePD" or "DLITE"

    Returns:
        xarray: Deepthought summary outputs and prob metrics
                dim basetime/prognosis_period
    """

    # get deepthought forecast from the archive
    try:
        dt_ds = get_dt_output(station, dt_start, dt_end, predictand, source='S3', dt_kind=dt_kind, output=None)
    except:
        print(f"No ePD data for station {station}")
        return

    # obs_ds = get_obs(station, dt1, dt2, predictand) # need to query DDB + QC + interp... TODO
    # need to return a serie of obs, index datetime
    # For now, patch to read the 2022 temperature extract from DT (QCed)
    # obs_ds = pd.read_parquet('s3://metservice-research-us-west-2/research/experiments/benv/mlpp/data_parquet/obs_TTTTT_2022.parquet')
    # obs_ds = obs_ds[obs_ds.index==station]
    # obs_ds = obs_ds.assign(validtime = lambda x : pd.to_datetime(x['forecast_time'])).set_index('validtime')

    # obs from DDB
    obs_ds = get_obs_serie(station,
                            dt_kind,
                            predictand,
                            'DDB_obs',
                            dt_start,
                            dt_end + datetime.timedelta(days=16), # add 16 days to cover the prognosis period
                            freq='hourly')
    
    # observation mapping
    # mapping = dict(zip(pd.to_datetime(obs_ds.index), obs_ds[predictand]))
    mapping = dict(zip(pd.to_datetime(obs_ds.time.values), obs_ds.values))
    map_func = np.vectorize(lambda x: mapping.get(x, np.nan))

    # apply the mapping function to the 'validtime' variable 
    obs_predictand = map_func(pd.to_datetime(dt_ds['validtime'].values)).astype(np.float32)
    # assign with the same dimensions
    dt_ds[f'obs_{predictand}'] = (('basetime', 'prognosis_period'), obs_predictand)
    # add metadata
    dt_ds[f'obs_{predictand}'].attrs = obs_ds.attrs

    # if dt_kind=='ePD':
    # full prob distribution
    if dt_ds.attrs['pdf_type']==3:
        # observation probabiltiy
        p_obs = xr.apply_ufunc(np.interp,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds['pdf'].isel(pdf_parameter=0),
                        dt_ds['pdf'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['p_obs'] = p_obs.astype(np.float32)

        # negative log likelihood
        dt_ds['negloglik'] = -np.log(dt_ds['p_obs'])

        # cumulative proba (for PIT histogram)
        cp_obs = xr.apply_ufunc(np.interp,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds['cdf'].isel(pdf_parameter=0),
                        dt_ds['cdf'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['cp_obs'] = cp_obs.astype(np.float32)

        # crps
        crps = xr.apply_ufunc(ps.crps_ensemble,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds['pdf'].isel(pdf_parameter=0),
                        dt_ds['pdf'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['crps'] = crps.astype(np.float32)

    # elif dt_kind=='DLITE':
    # normal distribution (mean + sd)
    elif dt_ds.attrs['pdf_type']==8:
        # observation probabiltiy (for the normal dist)
        p_obs = xr.apply_ufunc(norm.pdf,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=0),
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['p_obs'] = p_obs.astype(np.float32)

        # negative log likelihood
        dt_ds['negloglik'] = -np.log(dt_ds['p_obs'])

        # cumulative proba (for PIT histogram)
        cp_obs = xr.apply_ufunc(norm.cdf,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=0),
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['cp_obs'] = cp_obs.astype(np.float32)

        # crps
        crps = xr.apply_ufunc(ps.crps_gaussian,
                        dt_ds[f'obs_{predictand}'],
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=0),
                        dt_ds[f'{predictand}_PDF_parameter'].isel(pdf_parameter=1),
                        exclude_dims=set(('pdf_index',)),
                        input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                        vectorize=True)
        dt_ds['crps'] = crps.astype(np.float32)

    return dt_ds[['validtime', f'obs_{predictand}', 'mean', 'var', 'std', 'p_obs', 'cp_obs', 'negloglik', 'crps']]



class VerifDT(VerifModelStation):
    """ Class for DT verification (ePD or DLITE):
    Args:
        station (str): WMO station id.
        dt_start (datetime.datetime): The start datetime.
        dt_end (datetime.datetime): The end datetime.
        predictand (str): DeepThought predictand requested (ex 'TTTTT')
        dt_kind (str): either "ePD" or "DLITE"
    """
    def __init__(self,
                 station_id,
                 dt_start,
                 dt_end,
                 obs_source,
                 model,
                 model_vars,
                 fcast_window=16,
                 freq='hourly',
                 api_key=None
                 ):
        super().__init__(station_id,
                         dt_start,
                         dt_end,
                         obs_source,
                         model,
                         model_vars,
                         fcast_window,
                         freq,
                         api_key)
        # obs query
        self.obs_ds = super().query_obs()

        self.verif_ds_list = []

    def verify_vars(self):
        """ DeepThought Prob verification 
            Outputs a list of xr dataset for each requested model_var
        """

        for model_var in self.model_vars:
            # get deepthought forecast from the archive
            try:
                dt_ds = get_dt_output(self.station_id,
                                    self.dt_start,
                                    self.dt_end,
                                    model_var,
                                    source='S3',
                                    dt_kind=self.model,
                                    output=None)
            except:
                print(f"No {self.model} data for station {self.station_id}/{model_var}")
                return
    
            # observation mapping
            mapping = dict(zip(pd.to_datetime(self.obs_ds.time.values),
                               self.obs_ds[f'{model_var}_obs'].values))
            map_func = np.vectorize(lambda x: mapping.get(x, np.nan))

            # apply the mapping function to the 'validtime' variable 
            obs_predictand = map_func(pd.to_datetime(dt_ds['validtime'].values)).astype(np.float32)
            # assign with the same dimensions
            dt_ds[f'{model_var}_obs'] = (('basetime', 'prognosis_period'), obs_predictand)
            # add metadata
            dt_ds[f'{model_var}_obs'].attrs = self.obs_ds[f'{model_var}_obs'].attrs

            # if dt_kind=='ePD':
            # full prob distribution
            if dt_ds.attrs['pdf_type']==3:
                # observation probabiltiy
                p_obs = xr.apply_ufunc(np.interp,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds['pdf'].isel(pdf_parameter=0),
                                dt_ds['pdf'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['p_obs'] = p_obs.astype(np.float32)

                # negative log likelihood
                dt_ds['negloglik'] = -np.log(dt_ds['p_obs'])

                # cumulative proba (for PIT histogram)
                cp_obs = xr.apply_ufunc(np.interp,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds['cdf'].isel(pdf_parameter=0),
                                dt_ds['cdf'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['cp_obs'] = cp_obs.astype(np.float32)

                # crps
                crps = xr.apply_ufunc(ps.crps_ensemble,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds['pdf'].isel(pdf_parameter=0),
                                dt_ds['pdf'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['crps'] = crps.astype(np.float32)

            # elif dt_kind=='DLITE':
            # normal distribution (mean + sd)
            elif dt_ds.attrs['pdf_type'] in [0,8]:
                # observation probabiltiy (for the normal dist)
                p_obs = xr.apply_ufunc(norm.pdf,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=0),
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['p_obs'] = p_obs.astype(np.float32)

                # negative log likelihood
                dt_ds['negloglik'] = -np.log(dt_ds['p_obs'])

                # cumulative proba (for PIT histogram)
                cp_obs = xr.apply_ufunc(norm.cdf,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=0),
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['cp_obs'] = cp_obs.astype(np.float32)

                # crps
                crps = xr.apply_ufunc(ps.crps_gaussian,
                                dt_ds[f'{model_var}_obs'],
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=0),
                                dt_ds[f'{model_var}_PDF_parameter'].isel(pdf_parameter=1),
                                exclude_dims=set(('pdf_index',)),
                                input_core_dims=[[], ["pdf_index"], ["pdf_index"]],
                                vectorize=True)
                dt_ds['crps'] = crps.astype(np.float32)

            self.verif_ds_list.append(dt_ds[['validtime', f'{model_var}_obs', 'mean', 'var', 'std', 'p_obs', 'cp_obs', 'negloglik', 'crps']])
        
        return self.verif_ds_list