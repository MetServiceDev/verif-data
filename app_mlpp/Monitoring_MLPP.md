# MLPP Monitoring App

Monitoring App for MLPP models, against NWP (currently only WRF NZ4k) and Observations.

This web app sources the data from AWS S3, then valid credentials are required on the machine running the app.

```git clone git@github.com:MetServiceDev/verif-data.git```

## Install and Run 

In a fresh python env, from the app_mlpp folder:

```pip install -r requirements.txt```

```streamlit run mlpp_monitoring.py --server.port 8502```

Then in a browser : http://localhost:8502/

## Using Docker

Build the image from the app_mlpp folder:

```docker build -t monitoring_mlpp .``` 

To run the app locally

```docker run -p 81:81 -v ~/.aws/:/root/.aws/ monitoring_mlpp ```
