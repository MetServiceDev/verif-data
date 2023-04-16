import streamlit as st
import pandas as pd
import glob
import numpy as np

st.set_page_config(
    page_title="Verification App",
    page_icon="random",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "FR&D Verification App"
    }
)

st.write("# Probabilistic Post-Processing Verification 📊")

st.markdown(
    """
    Verification App for ePD vs. Machine Learning Post-Processing experiments
"""
)

st.session_state["data_path"] = '/home/benv/data/verification'

st.session_state["year"] = st.selectbox("Select an analysis year", ['2022'])
st.session_state["predictand"] = st.selectbox("Select a forecast variable", ['TTTTT'])
st.session_state["ref_model"] = st.selectbox("Select the model to compare to ePD", ['DRN2_ARWECMWFcld_single_nz4km'])
st.session_state["max_lead"] = st.selectbox("Select the maximum lead time (h)", [85])

# Stations attributes
@st.cache_data
def load_station_attributes():
    st_att = pd.read_parquet(st.session_state["data_path"] + '/stations_attributes.parquet')
    return st_att

st.session_state["stations_attributes"] = load_station_attributes()

# Station list for models
st.session_state["model_path"] = f'{st.session_state["data_path"]}/{st.session_state["year"]}/{st.session_state["ref_model"]}/{st.session_state["predictand"]}'
st.session_state["model_station_list"] = [station.split('/')[-1:][0][:5] for station 
                                          in glob.glob(f'{st.session_state["model_path"]}/*.nc')]

st.session_state["epd_path"] = f'{st.session_state["data_path"]}/{st.session_state["year"]}/ePD/{st.session_state["predictand"]}'
st.session_state["epd_station_list"] = [station.split('/')[-1:][0][:5] for station 
                                          in glob.glob(f'{st.session_state["epd_path"]}/*.nc')]

# Stations mean by lead time
@st.cache_data
def load_mean_leadtime(model_path):
    _ds = pd.concat([pd.read_parquet(file).assign(stationId = file.split('/')[-1:][0][:5])
            for file in glob.glob(f'{model_path}/*_leadtime_mean.parquet')])
    _ds['lead_hour'] = _ds.index / np.timedelta64(1, 'h')
    return _ds

# st.session_state["model_leadtimes"] 
st.session_state["model_leadtimes"] = load_mean_leadtime(st.session_state["model_path"])
st.session_state["epd_leadtimes"] = load_mean_leadtime(st.session_state["epd_path"])


# Stations c_obs by station
# @st.cache_data
# def load_c_ops(model_path):
#     _ds = pd.concat([pd.read_parquet(file).reset_index()
#                        .assign(lead_hour = lambda x: x['prognosis_period'] / np.timedelta64(1, 'h'))
#         for file in glob.glob(f'{model_path}/*_cp_obs.parquet')])
#     _ds = _ds[_ds['lead_hour'] <= st.session_state["max_lead"]]
#     return _ds

# st.session_state["model_c_obs"] = load_c_ops(st.session_state["model_path"])
# st.session_state["epd_c_obs"] = load_c_ops(st.session_state["epd_path"])
