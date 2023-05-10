import streamlit as st
import glob
import xarray as xr
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np



data_path = st.session_state["data_path"]
year = st.session_state["year"]
predictand = st.session_state["predictand"]
ref_model = st.session_state["ref_model"]


# Ref Model station list
station_list = [station.split('/')[-1:][0][:5] for station 
                in glob.glob(f'{data_path}/{year}/ePD/{predictand}/*')] #.sort()

station_attributes = st.session_state["stations_attributes"][st.session_state["stations_attributes"]['stationId'].isin(station_list)]

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

    return _ds


# Title
st.header('Probabilistic Verification - Station Level Metrics')


# Selection widgets ##############################################
station_select = st.sidebar.selectbox("Select a station", station_attributes['stationId'])

st.write('Station :', station_attributes[station_attributes['stationId']==station_select])

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
station_model_leadtime = st.session_state["model_leadtimes"].loc[st.session_state["model_leadtimes"]['stationId']==station_select]
station_epd_leadtime = st.session_state["epd_leadtimes"].loc[st.session_state["epd_leadtimes"]['stationId']==station_select]


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

layout = go.Layout(
    title='Time Serie - DRN vs. ePD - Mean +/- SD ',
    xaxis=dict(title='Valid Time'),
    yaxis=dict(title=predictand)
)

fig1 = go.Figure(data=[trace11, trace12, trace13], layout=layout)
fig1.update_xaxes(range=[drn_station_basetime['validtime'].min(), drn_station_basetime['validtime'].max()])
st.plotly_chart(fig1,use_container_width=True)



col1, col2 = st.columns(2)

with col1:
    # CRPS Plot ##########################################
    trace31 = go.Scatter(x=station_model_leadtime['lead_hour'],
                        y=station_model_leadtime['crps'],
                        mode='lines',
                        name=ref_model )

    trace32 = go.Scatter(x=station_epd_leadtime['lead_hour'],
                        y=station_epd_leadtime['crps'],
                        mode='lines',
                        name='ePD' )

    layout = go.Layout(
            title='Mean Continous Ranked Probability Score',
            xaxis=dict(title='Lead Time Hour'),
            yaxis=dict(title='Deg C')
    )

    fig3 = go.Figure(data=[trace31, trace32], layout=layout)
    fig3.update_xaxes(range=[station_model_leadtime['lead_hour'].min(), station_model_leadtime['lead_hour'].max()])
    st.plotly_chart(fig3,use_container_width=False)

with col2:
    # MAE Plot ##########################################
    trace1 = go.Scatter(x=station_model_leadtime['lead_hour'],
                        y=station_model_leadtime['mae'],
                        mode='lines',
                        name=f'{st.session_state["ref_model"]} - mean' )


    trace2 = go.Scatter(x=station_epd_leadtime['lead_hour'],
                        y=station_epd_leadtime['mae'],
                        mode='lines',
                        name='ePD - Mean' )

    trace3 = go.Scatter(x=station_model_leadtime['lead_hour'],
                        y=station_model_leadtime['nwp_mae'],
                        mode='lines',
                        name='NWP' )

    layout = go.Layout(
        title='MAE',
        xaxis=dict(title='Lead Time Hour'),
        yaxis=dict(title='Deg C')
    )

    # create plot figure with multiple line plot traces
    fig2 = go.Figure(data=[trace1, trace2, trace3], layout=layout)
    fig2.update_xaxes(range=[0 ,st.session_state["max_lead"]])
    st.plotly_chart(fig2,use_container_width=False)





# PIT histogram ###########################
trace21 = go.Histogram(x=drn_station_pit,
                      xbins=dict(start=0, end=1, size=0.1),
                      histnorm='percent',
                      name=ref_model )

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

layout = go.Layout(
    title='PIT Histogram - DRN vs. ePD',
    xaxis=dict(title='Forecast Probability Quantile'),
    yaxis=dict(title='% of Observed'),
    shapes=[hline]
)

fig2 = go.Figure(data=[trace21, trace22], layout=layout)
st.plotly_chart(fig2,use_container_width=False)




