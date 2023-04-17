# Verification App

## Run

From the app folder : ```streamlit run verif_app.py```

Then on a browser from the corporate network : http://10.200.2.116:8501/

## Docker

To build the image:

```docker build -t verif_app .``` from the app folder

To run the app from the image from the workstation 

```docker run -p 80:80 -v /home/benv/data/:/home/benv/data/ verif_app ```