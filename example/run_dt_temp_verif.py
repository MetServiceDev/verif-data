import datetime
from verif.data.obs import ddb
from verif.dt.dt_verif import verify_dt_ouput
from dt_output import get_dt_output

import numpy as np
import pandas as pd
import xarray as xr

import s3fs
import json
import os
import boto3
from tqdm import tqdm

fs_s3 = s3fs.S3FileSystem()

s3_mlpp = 's3://metservice-research-us-west-2/research/experiments/benv/mlpp'

s3 = boto3.client('s3')

def main():

    stations_nz_2022  = json.load(fs_s3.open(
                            s3_mlpp + '/data_parquet/valid_obs_stations.json'))['TTTTT']['2022']


    station_list = [station for station in stations_nz_2022
        if fs_s3.exists(f'{s3_mlpp}/data_parquet/2022/ARWECMWFcld_single_nz4km/{station}.parquet')]


    dt_start = datetime.datetime(2022,1, 1)
    dt_end = datetime.datetime(2022,12, 31)

    predictand='TTTTT'
    dt_kind='ePD'

    for station in tqdm(station_list):
        ds_verif = verify_dt_ouput(station, dt_start, dt_end, predictand, dt_kind)
        if ds_verif:
            ds_verif.to_netcdf('./temp.nc')
            s3.upload_file('./temp.nc',
                        'metservice-research-us-west-2'
                        , f'research/experiments/benv/mlpp/verification/2022/ePD/TTTTT/{station}.nc')
            

if __name__ == "__main__":
    main()
