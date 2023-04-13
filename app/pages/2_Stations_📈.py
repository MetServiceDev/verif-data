import streamlit as st
import glob
import xarray as xr
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
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

st.cache_data.clear()
st.cache_resource.clear()


# Ref Model station list
station_list = [station.split('/')[-1:][0][:5] for station 
                in glob.glob(f'{data_path}/{year}/{ref_model}/{predictand}/*')] #.sort()


@st.cache_resource
def load_station(model, station, basetimes_hours=None, prog_periods=None):
    """
    Args
        basetimes_hours : like [0,12]
        prog_periods : max like 85
    """
    _ds = xr.open_dataset(f'{data_path}/{year}/{model}/{predictand}/{station}.nc',
                        engine='netcdf4')
  
    if basetimes_hours is not None:
        _ds =  _ds.sel(basetime=pd.to_datetime(_ds['basetime'].values).hour.isin(basetimes_hours))
    if prog_periods is not None:
        _ds = _ds.isel(prognosis_period=slice(0, prog_periods))

    # _ds['mae'] = np.abs(_ds['mean'] - _ds[f'obs_{predictand}'])
    # ds_lead = _ds.groupby('prognosis_period').mean(dim='basetime').to_dataframe()
    return _ds #, ds_lead

# @st.cache_data
# def station_lead(_ds):
#     """
#     """
#     _ds['mae'] = np.abs(_ds['mean'] - _ds[f'obs_{predictand}'])
#     ds_lead = _ds.groupby('prognosis_period').mean(dim='basetime').to_dataframe()
#     return ds_lead


# Selection widgets ##############################################
station_select = st.sidebar.selectbox("Select a station", station_list)

basetime_values = load_station(ref_model, station_select)['basetime'].values

basetime_select = st.sidebar.select_slider("Basetime",
                                           basetime_values
                                        )

# Data Load #######################################################
# load station set for DRN
drn_station = load_station(ref_model, station_select)
drn_station_basetime = drn_station.sel(basetime=basetime_select).to_dataframe()
# drn_station_lead = station_lead(drn_station)

# load station for ePD (subset)
ePD_station = load_station('ePD', station_select, basetimes_hours=[0,12], prog_periods=85)
# ePD_station = ePD_station.isel(prognosis_period=slice(0,85))
ePD_station_basetime =  ePD_station.sel(basetime=basetime_select).to_dataframe()
# ePD_station_lead = station_lead(ePD_station)

# pit
drn_station_pit = drn_station['cp_obs'].values.flatten()
epd_station_pit = ePD_station['cp_obs'].values.flatten()

# grouped by lead time values
# drn_station['mae'] = np.abs(drn_station['mean'] - drn_station[f'obs_{predictand}'])
# drn_station_lead = drn_station.groupby('prognosis_period').mean(dim='basetime').to_dataframe()

# ePD_station['mae'] = np.abs(ePD_station['mean'] - ePD_station[f'obs_{predictand}'])
# ePD_station_lead = ePD_station.groupby('prognosis_period').mean(dim='basetime').to_dataframe()

# Time Serie Plot ##########################################
trace11 = go.Scatter(x=drn_station_basetime['validtime'],
                    y=drn_station_basetime['mean'],
                    mode='lines',
                    error_y = dict(array= drn_station_basetime['std']),
                    name=ref_model)

trace12 = go.Scatter(x=ePD_station_basetime['validtime'],
                    y=ePD_station_basetime['mean'],
                    mode='lines',
                    error_y = dict(array= ePD_station_basetime['std']),
                    name='ePD' )

trace13 = go.Scatter(x=drn_station_basetime['validtime'],
                    y=drn_station_basetime['obs_TTTTT'],
                    mode='lines',
                    name='Obs' )


# create plot layout
layout = go.Layout(
    title='Time Serie - DRN vs. ePD - Mean +/- SD ',
    xaxis=dict(title='Valid Time'),
    yaxis=dict(title=predictand)
)

# create plot figure with multiple line plot traces
fig1 = go.Figure(data=[trace11, trace12, trace13], layout=layout)
fig1.update_xaxes(range=[drn_station_basetime['validtime'].min(), drn_station_basetime['validtime'].max()])
st.plotly_chart(fig1,use_container_width=True)


# PIT histogram ###########################
trace21 = go.Histogram(x=drn_station_pit,
                      xbins=dict(start=0, end=1, size=0.1),
                      histnorm='percent',
                      name='DRN' )

trace22 = go.Histogram(x=epd_station_pit,
                      xbins=dict(start=0, end=1, size=0.1),
                      histnorm='percent',
                      name='ePD' )

hline = go.layout.Shape(
    type='line',
    x0=0,
    y0=10, # y-value where the line should be drawn
    x1=1,
    y1=10, # y-value where the line should be drawn
    line=dict(color='red', width=2)
)

# create plot layout
layout = go.Layout(
    title='PIT Histogram - DRN vs. ePD',
    xaxis=dict(title='PIT'),
    yaxis=dict(title='% of Observed'),
    shapes=[hline]
)

# create plot figure with multiple line plot traces
fig2 = go.Figure(data=[trace21, trace22], layout=layout)
st.plotly_chart(fig2,use_container_width=False)




# CRPS Plot ##########################################
trace31 = go.Scatter(x=drn_station_lead.index,
                    y=drn_station_lead['crps'],
                    mode='lines',
                    name='DRN' )

trace32 = go.Scatter(x=ePD_station_lead.index,
                    y=ePD_station_lead['crps'],
                    mode='lines',
                    name='ePD' )

# trace13 = go.Scatter(x=drn_station_basetime['validtime'],
#                     y=drn_station_basetime['obs_TTTTT'],
#                     mode='lines',
#                     name='Obs' )


# create plot layout
layout = go.Layout(
    title='Time Serie - DRN vs. ePD - Mean +/- SD ',
    xaxis=dict(title='Valid Time'),
    yaxis=dict(title=predictand)
)

# create plot figure with multiple line plot traces
fig3 = go.Figure(data=[trace31, trace32], layout=layout)
#fig3.update_xaxes(range=[drn_station_basetime['validtime'].min(), drn_station_basetime['validtime'].max()])
st.plotly_chart(fig3,use_container_width=False)