import streamlit as st
import pandas as pd

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
                 

@st.cache_data
def load_station_attributes():
    st_att = pd.read_parquet(st.session_state["data_path"] + '/stations_attributes.parquet')
    return st_att

st.session_state["stations_attributes"] = load_station_attributes()
