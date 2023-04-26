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
# Extract a specific variable
obs_gust = ddb.extract_obs_data(obs_all, 
                                var_name="windGustMaximum@1h",
                                freq="hourly")
```

### 1 Minute Obs API

```python
import datetime
from verif.obs import obsAPI

api = obsAPI.RequestAPI(station_id=93106, apikey="1234567890")
api.query_last(60)
api.query_range(datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 2))
```


## Models Verification

The folowing models are covered and the following functions create verification dataset against the chosen Obs source ('DDB_obs' or 'API_obs').

### DeepThought

DeepThought verification is currently done against DDB obs source. The model outputs are pulled from S3 thanks to the `dt-output` package.

The `VerifDT.verify_vars()` returns an list of Xarray dataset with PDF and CDF values for the observations and probabilistic verification metrics (CRPS, Negative log Likelihood) of the considered model variables to verify.

```python
import datetime
from verif.models.dt_verif import VerifDT

verif_dlite = dt_verif.VerifDT(station_id='93439',
                                      dt_start=datetime.datetime(2023, 3, 1),
                                      dt_end=datetime.datetime(2023, 3, 2),
                                      obs_source='DDB_obs',
                                      model='DLITE',
                                      model_vars=['TTTTT', 'fff10'])

# Run the verification
verif_dlite.verify_vars()
```

### WRF

TBD

### MLPP

TBD

#### Windcast

TBD