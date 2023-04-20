"""
Functions for querying the DynamoDB table for observations.

"""

from . import resource_ddb, TABLE_NAME, TABLE_NAME_recent
from .. import get_loggers
from boto3.dynamodb.conditions import Key
import datetime
import numpy as np
import xarray as xr


logger = get_loggers()

def get_obs_all(obs_id: str, dt_start: datetime.datetime, dt_end: datetime.datetime, table_recent: bool = False):
    """Get all observations from the DynamoDB table for a given obs_id and time range.

    Args:
        obs_id (str): The obs_id to query.
        dt_start (datetime.datetime): The start datetime.
        dt_end (datetime.datetime): The end datetime.
        table_recent (bool, optional): If True, also query the recent table. Defaults to False.

    Returns:
        list: A list of dictionaries containing the observations.
    """
    # convert datetime to string
    dt_0 = datetime.datetime.strftime(dt_start, "%Y%m%d%H%M%S")
    dt_1 = datetime.datetime.strftime(dt_end, "%Y%m%d%H%M%S")

    ddb_tables = [TABLE_NAME.format(year=year) for year in range(dt_start.year, dt_end.year + 1)]
    if table_recent:
        ddb_tables = ddb_tables + [TABLE_NAME_recent] 

    # query the DynamoDB tables

    result = []
    for ddb_table_name in ddb_tables:
        # query the table for the obs_id and time range of interest
        ddb_table = resource_ddb.Table(ddb_table_name)
        response = ddb_table.query(
            KeyConditionExpression=Key("obs_id").eq(obs_id)
            & Key("valid_time").between(dt_0, dt_1)
        )
        result.extend(response["Items"])

        # if there are more than 1MB of data, then we need to query again
        while "LastEvaluatedKey" in response:
            response = ddb_table.query(
                KeyConditionExpression=Key("obs_id").eq(obs_id)
                & Key("valid_time").between(dt_0, dt_1),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            result.extend(response["Items"])

    return result


def extract_obs_data(obs_all: list, var_name: str, freq: str):
    """Extract the data from the observations.

    Args:
        obs_all (list): all observations queried from the DynamoDB table
        var_name (str): variable name
        freq (str): frequency of the data

    Returns:
        DataArray: xarray DataArray containing the data
    """
    valid_time = []
    data = []
    for obs in obs_all:
        dt = datetime.datetime.strptime(obs["valid_time"], "%Y%m%d%H%M%S")
        if freq == "hourly":
            if dt.minute == 0:
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

    da = xr.DataArray(
        data,
        coords={
            "time": valid_time,
        },
        dims=["time"],
    )

    return da
