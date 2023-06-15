# Verification App

## Run

From the app folder : ```streamlit run verif_app_mlpp.py --server.port 8502```

Then on a browser from the corporate network : http://10.200.2.116:8501/

## Docker

Build the image:

```docker build -t monitoring_mlpp .``` from the app_mlpp folder

To run the app locally

```docker run -p 80:80 -v /home/benv/data/:/home/benv/data/ monitoring_mlpp ```