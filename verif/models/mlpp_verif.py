
"""
MLPP verification class

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


class VerifMLPP(VerifModelStation):
    """ Class for MLPP verification: Probabilistic Verification CRPS of NWP models postprocessed 
        forecast variables.
    Args:
        station (str): WMO station id.
        fcast_window (int): number of days to include in the obs windows after dt_end
        obs_source (str): obs data source ('DDB_obs', 'API_obs')
        model (str): model to verify (need to be referenced in the Yaml)
        model_vars (list): list of model variables we want to verify
        preds_ds (pd.DataFrame) : dataframe with predictions and forecast time
        freq (str): frequency requested (None: all points, 'hourly', '10min' )
        api_key (str): 1 min obs API key

    Methods:
        verify_vars(self):
            Computes verification metrics for each model variable to verify.
            Returns a list of datasets containing the verification results.
    """
    def __init__(self,
                 station_id,
                 obs_source,
                 model,
                 model_vars,
                 preds_ds,
                 fcast_window=16,
                 freq='hourly',
                 api_key=None
                 ):
           
        self.preds_ds = preds_ds
        dt_start = preds_ds['forecast_time'].min()
        dt_end = preds_ds['forecast_time'].max()

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

        # join with obs
        self.verif_ds = (self.preds_ds.set_index('forecast_time')
                        .join(self.obs_ds.to_dataframe().tz_localize(tz='UTC')))
        
        # verification metrics for each var to verify
        for var in self.model_vars:
            verif_var = self.verif_ds.assign(error = lambda x: x[f'p1_{var}'] - x[f'{var}_obs'],
                                abs_error = lambda x: np.abs(x.error),
                                error2 = lambda x: x.error**2,
                                p_obs = lambda x: norm.pdf(x[f'{var}_obs'], x[f'p1_{var}'], x[f'p2_{var}']),
                                cp_obs = lambda x: norm.pdf(x.TTTTT_obs, x[f'p1_{var}'], x[f'p2_{var}']),
                                negloglik = lambda x: -np.log(x.p_obs),
                                crps = lambda x: ps.crps_gaussian(x[f'{var}_obs'], x[f'p1_{var}'], x[f'p2_{var}']),
                                )

            self.verif_ds_list.append(verif_var)
                        
        return self.verif_ds_list