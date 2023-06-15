import numpy as np
import pandas as pd
import streamlit as st
import s3fs
import datetime
import plotly.express as px
import plotly.graph_objs as go

fs_s3 = s3fs.S3FileSystem()

st.set_page_config(
    page_title="Verification App for MLPP",
    page_icon="random",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "FR&D MLPP Verification App"
    }
)

st.sidebar.image('./img/metservice_logo.png', width=300)

st.sidebar.write("# MLPP Monitoring")

st.sidebar.markdown(
    """
    Monitoring of Post-Processed NWP models
    """
    )

VERIF_DATA_PATH = 's3://metservice-research-us-west-2/research/experiments/benv/mlpp/verification'


# # Stations attributes
@st.cache_data(persist='disk')
def load_station_attributes():
    st_att = (pd.read_parquet('s3://metservice-research-us-west-2/research/experiments/benv/mlpp/data_parquet/stations_attributes.parquet')
                .sort_values(by='stationId'))
    return st_att
station_attributes = load_station_attributes()

# Model and Runs Selection
model = st.sidebar.selectbox(label='Model',
                            options=['nz4kmN-ECMWF-SIGMA'], #[run.split('/')[-1] for run in fs_s3.glob(f'{VERIF_DATA_PATH}/')],
                            )

fcast_var = st.sidebar.selectbox(label='Forecast Variable',
                            options=['t2mc'],
                            )


st.sidebar.markdown(
    """
    Select one or multiple runs in the time window to compute summary metrics:
    """
    )

available_runs = [int(run.split('/')[-1]) for run in fs_s3.glob(f'{VERIF_DATA_PATH}/{model}/')]

time_window = st.sidebar.select_slider(label='Time Window',
                            options=available_runs,
                            value = (min(available_runs), max(available_runs)))

runs = st.sidebar.multiselect(label='Runs for Summary Metrics',
                            options=['All'] + [run for run in available_runs if run>=time_window[0] and run<=time_window[1]],
                            )
if "All" in runs:
    runs = [run for run in available_runs if run>=time_window[0] and run<=time_window[1]]

runs.sort(reverse=True)

# load run files 
@st.cache_data(persist='disk')
def load_files(model, run):
    files = fs_s3.glob(f'{VERIF_DATA_PATH}/{model}/{run}/')
    verif_run = pd.concat([(pd.read_parquet(f's3://{file}',
                              columns = ['base_time', 'forecast_time','prognosis_hour', 't2mc', 'p1_TTTTT', 'p2_TTTTT',
                                         'TTTTT_obs', 'TTTTT_cp_obs','TTTTT_crps'])
                               .assign(stationId = file.split('/')[-1][:5])
                               .assign(run = str(run)) )
                                for file in files])
    return verif_run

# load station files 
@st.cache_data(persist='disk')
def load_station_file(model, run, station):
    station_ds = pd.read_parquet(f's3://{VERIF_DATA_PATH}/{model}/{run}/{station}.parquet')
    return station_ds

# load summary files 
@st.cache_data(persist='disk')
def load_summary_files(model, run, type='lead_time'):
    sum_file = pd.read_parquet(f's3://{VERIF_DATA_PATH}/{model}/{run}/{type}_{run}.parquet')
    return sum_file


my_bar = st.sidebar.progress(0, text='Loading Summary Files From S3')
lead_time_sum_ds = pd.DataFrame()
stations_sum_ds = pd.DataFrame()
for i, run in enumerate(runs):
    lead_time_sum_ds = pd.concat([lead_time_sum_ds, load_summary_files(model, run, type='lead_time')])
    stations_sum_ds = pd.concat([stations_sum_ds, load_summary_files(model, run, type='stations')])
    my_bar.progress((i+1)/len(runs), text='Loading Summary Files From S3')


if len(lead_time_sum_ds)>0:

    # Group by Run
    st.header('Overall Performance by Run')
    verif_run_ds = lead_time_sum_ds.groupby('run').mean()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('CRPS and Negative Log Likelihood')
        st.line_chart(verif_run_ds[['TTTTT_crps', 'TTTTT_negloglik']])
    with col2:
        st.subheader('MAE')
        st.line_chart(verif_run_ds[['nwp_ae', 'TTTTT_abs_error']])
    with col3:
        st.subheader('Bias')
        st.line_chart(verif_run_ds[['nwp_e', 'TTTTT_error']])
    
    # Group by LeadTime
    st.header('Overall Performance by Lead Time')
    verif_leadtime_ds = lead_time_sum_ds.groupby('prognosis_hour').mean()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('CRPS and Negative Log Likelihood')
        st.line_chart(verif_leadtime_ds[['TTTTT_crps', 'TTTTT_negloglik']])
    with col2:
        st.subheader('MAE')
        st.line_chart(verif_leadtime_ds[['nwp_ae', 'TTTTT_abs_error']])
    with col3:
        st.subheader('Bias')
        st.line_chart(verif_leadtime_ds[['nwp_e', 'TTTTT_error']])


    # Group by Station
    st.header('Overall Performance by Station')
    verif_stations_ds = (stations_sum_ds.groupby('station_id').mean()
                            .merge(station_attributes, left_index=True, right_on='stationId'))


    col1, col2 = st.columns(2)
    with col1:
        # WRF MAE Map
        fig = px.scatter_mapbox(verif_stations_ds, lat="latitude", lon="longitude", color="nwp_ae", hover_data=["wmoId", "name"],
                                color_continuous_scale='balance', height=600)
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=4,
            # mapbox_center={"lat": 37.7749, "lon": -122.4194}
        )
        fig.update_layout(title=f'MAE - {model} - {fcast_var}')
        st.plotly_chart(fig,use_container_width=False)

    with col2:
        # CRPS Map
        fig = px.scatter_mapbox(verif_stations_ds, lat="latitude", lon="longitude", color="TTTTT_crps", hover_data=["wmoId", "name"],
                                color_continuous_scale='balance', height=600)
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=4,
            # mapbox_center={"lat": 37.7749, "lon": -122.4194}
        )
        fig.update_layout(title=f'Mean CRPS - MLPP')
        st.plotly_chart(fig,use_container_width=False)

    # PIT histogram ###########################
    # trace21 = go.Histogram(x=verif_ds['TTTTT_cp_obs'].values.flatten(),
    #                     xbins=dict(start=0, end=1, size=0.1),
    #                     histnorm='percent',
    #                     name=model )

    # hline = go.layout.Shape(
    #     type='line',
    #     x0=0,
    #     y0=10, # y-value where the line should be drawn
    #     x1=1,
    #     y1=10, # y-value where the line should be drawn
    #     line=dict(color='red', width=2)
    # )

    # layout = go.Layout(
    #     title='PIT Histogram - DRN',
    #     xaxis=dict(title='Forecast Probability Quantile'),
    #     yaxis=dict(title='% of Observed'),
    #     shapes=[hline]
    # )

    # fig2 = go.Figure(data=[trace21], layout=layout)
    # st.plotly_chart(fig2,use_container_width=False)



    # Station Level
    st.sidebar.markdown(
    """
    Select one run for station time serie:
    """
    )

    st.header('Station Time Serie')
    run_station = st.sidebar.selectbox(label='Run for Station Time Serie',
                                    options=runs)
                                    # format_func= lambda x: datetime.datetime(int(x[:4]), int(x[4:6]), int(x[6:8]), int(x[8:10]))

    stations = [file.split('/')[-1][0:5] for file in fs_s3.glob(f'{VERIF_DATA_PATH}/{model}/{run_station}/[0-9]*.parquet')]

    station = st.sidebar.selectbox(label='Station',
                                options=stations,
                                index=0,
                                format_func= lambda x: station_attributes[station_attributes['stationId']==x]['name'].values[0]
                                )

    

    verif_ds_station = load_station_file(model, run_station, station)



    # Display Station Attributes
    st.table(station_attributes[station_attributes['stationId']==station][['stationId','name','latitude',
                            'longitude','elevation','icaoId','countryCode','offsetToUTC','grid_elev_nz4km']])

    # Time Serie Plot ##########################################
    trace11 = go.Scatter(x=verif_ds_station.index,
                        y=verif_ds_station['p1_TTTTT'],
                        mode='lines',
                        error_y = dict(array= verif_ds_station['p2_TTTTT']),
                        name=model)

    trace12 = go.Scatter(x=verif_ds_station.index,
                        y=verif_ds_station['t2mc'],
                        mode='lines',
                        name='NWP' )

    trace13 = go.Scatter(x=verif_ds_station.index,
                        y=verif_ds_station['TTTTT_obs'],
                        mode='lines',
                        name='Obs' )

    layout = go.Layout(
        title=f'Time Serie - Mean +/- SD ',
        xaxis=dict(title='Valid Time'),
        yaxis=dict(title=fcast_var)
    )

    fig1 = go.Figure(data=[trace11, trace12, trace13], layout=layout)
    fig1.update_xaxes(range=[verif_ds_station.index.min(), verif_ds_station.index.max()])
    st.plotly_chart(fig1,use_container_width=True)


if st.sidebar.button("Clear Cache"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_data.clear()