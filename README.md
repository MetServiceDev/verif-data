# Verification Data

Data processing package for verification purposes.

The main objective of this package is the generation of datasets for verification purposes (metrics, reports, alerts, visualisations...), by merging model outputs (ML or NWP) and corresponding observations values.


## Models output vs. Observations Variables

The models (ePD, DLITE, WRF, MLPP...) outputs to verify against an observation variable are defined in the configuration  ```data/obs_var.yaml``` file.
Each model variable is given with their unit and the corresponding source obs variable, unit and conversion factor/delta.

Example for the ePD model:

```yaml
ePD:
  TTTTT:
    unit: degC
    DDB_obs:
      airTemperature:
        unit: K
        conv: [1,-273.15]
    API_obs:
      airtemp_01mnavg:
        unit: degC
        conv: [1,0]
  fff10:
    unit: kt
    DDB_obs:
      windSpeed@1h:
        unit: m/s
        conv: [1.944,0]
    API_obs:
      windspd_01hravg:
        unit: kt
        conv: [1,0] 
```

## Utils



## Observations

For now, 2 datasources are covered: DynamoDB and the 1 min API

The folowing gives examples how to use the Obs retrieval functions idependently.

### Dynamo DB

```python
import datetime
from verif.obs import ddb 

# Query the station for a time period
obs_all = ddb.get_obs_all(obs_id = "NZCQX_nzaws",
                          dt_start = datetime.datetime(2023, 3, 1),
                          dt_end = datetime.datetime(2023, 3, 30),
                          table_recent=True)
# Extract a variable at frequency
obs_gust_all = ddb.extract_obs_data(obs_all, 
                                var_name="windGustMaximum@1h")
obs_gust_hour = ddb.extract_obs_data(obs_all, 
                                var_name="windGustMaximum@1h",
                                freq="hourly")
obs_gust_10min = ddb.extract_obs_data(obs_all, 
                                var_name="windGustMaximum@1h",
                                freq="10min")
```

### 1 Minute Obs API

```python
import datetime
from verif.obs import obsAPI

# Instantiate the class for the station with the API key
api = obsAPI.RequestAPI(station_id=93106, apikey="1234567890")
# Query last 60 minutes (max 360) - return a dict
api.query_last(60)
# Query a range - More than one day possible
api.query_range(datetime.datetime(2023, 3, 1), datetime.datetime(2023, 3, 4))
# Extract a variable at frequency
obs_temp_all = api.extract_obs_data('airtemp_01mnavg')
obs_temp_hour = api.extract_obs_data('airtemp_01mnavg',
                                     freq='hourly')
obs_temp_10min= api.extract_obs_data('airtemp_01mnavg',
                                     freq='10min')

```


## Models Verification

The folowing models are covered and the following functions create verification dataset against the chosen Obs source ('DDB_obs' or 'API_obs').

### Generic Class

The parent generic class ```VerifModelStation``` allows to retrieve corresponding observations variables for a given model/outputs to verify. This class can be derived for model verification specifics.

```python
from verif.models import verif

# from DDB
verif_model = verif.VerifModelStation(station_id='93106',
                                      dt_start=datetime.datetime(2023, 3, 1),
                                      dt_end=datetime.datetime(2023, 3, 30),
                                      obs_source='DDB_obs',
                                      model='ePD',
                                      model_vars=['TTTTT','fff10'],
                                      fcast_window=16,
                                      freq='hourly')

# or from API
verif_model = verif.VerifModelStation(station_id='93106',
                                      dt_start=datetime.datetime(2023, 3, 1),
                                      dt_end=datetime.datetime(2023, 3, 30),
                                      obs_source='API_obs',
                                      model='ePD',
                                      model_vars=['TTTTT','fff10'],
                                      fcast_window=16,
                                      freq='hourly',
                                      api_key="1234567890")

# Retrive the obs
verif_model.query_obs()

```


### DeepThought

DeepThought verification can be done against DDB or API obs. The model outputs are pulled from S3 thanks to the `dt-output` package.

The `VerifDT.verify_vars()` returns an list of Xarray dataset with PDF and CDF values for the observations and probabilistic verification metrics (CRPS, Negative log Likelihood) of the considered model variables to verify.

```python
import datetime
from verif.models.dt_verif import VerifDT

verif_dlite = VerifDT(station_id='93439',
                      dt_start=datetime.datetime(2023, 3, 1),
                      dt_end=datetime.datetime(2023, 3, 2),
                      obs_source='DDB_obs',
                      model='DLITE',
                      model_vars=['TTTTT', 'fff10'])

# Run the verification (list of xarrays for each requested model vars)
verifs = verif_dlite.verify_vars()
```

### WRF

TBD

### MLPP

TBD

#### Windcast

TBD