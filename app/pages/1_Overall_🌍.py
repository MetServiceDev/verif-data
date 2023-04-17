import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


######### Data #########################################################
model_station_list = st.session_state["model_station_list"]
epd_station_list = st.session_state["epd_station_list"]


overall_model_leadtime = st.session_state["model_leadtimes"].groupby(st.session_state["model_leadtimes"].index).mean()
overall_epd_leadtime = st.session_state["epd_leadtimes"].groupby(st.session_state["epd_leadtimes"].index).mean()

# overall_model_station = (st.session_state["model_leadtimes"]
#                         .loc[st.session_state["model_leadtimes"].iloc[:st.session_state["max_lead"]].index]
#                         .groupby('stationId').mean() )

# overall_epd_station = (st.session_state["epd_leadtimes"]
#                         .loc[st.session_state["epd_leadtimes"].iloc[:st.session_state["max_lead"]].index]
#                         .groupby('stationId').mean() )


crpss = (st.session_state["epd_leadtimes"][['stationId', 'lead_hour', 'crps' ]]
        .merge(st.session_state["model_leadtimes"][['stationId', 'lead_hour', 'crps']],
            on=['stationId', 'lead_hour'],
            suffixes=('_epd', f'_{st.session_state["ref_model"]}'))
        .assign(crpss = lambda x: 1 - x[f'crps_{st.session_state["ref_model"]}']/x.crps_epd)
        )

crpss_lead = (crpss[['lead_hour','crps_epd', f'crps_{st.session_state["ref_model"]}','crpss']]
              .groupby('lead_hour').mean() )
crpss_station = (crpss[['stationId','crps_epd', f'crps_{st.session_state["ref_model"]}','crpss']]
                 .groupby('stationId').mean()
                 .join(st.session_state["stations_attributes"].set_index('stationId')))

models_prob_bins = (st.session_state["prob_bins"]
                    .sort_index().loc[(slice(int(st.session_state["max_lead"])), slice(None)), :] #filtering max lead
                    .groupby(['model'])
                    .apply(lambda x: x[['cp_obs_count','p_obs_count']].groupby(['bin']).sum() / x[['cp_obs_count','p_obs_count']].sum()) 
                    )


model_prob_bins_stations = (st.session_state["prob_bins"]
                            .sort_index().loc[(slice(int(st.session_state["max_lead"])), slice(None)), :] #filtering max lead
                            .groupby(['model','stationId'])
                            .apply(lambda x: x[['cp_obs_count','p_obs_count']].groupby(['bin']).sum() / x[['cp_obs_count','p_obs_count']].sum()) 
                            )



# Metrics
# col1, col2, col3 = st.columns(3)
# st.metric("Temperature", overall_model_leadtime['crps'].mean())
# st.metric("Wind", overall_epd_leadtime['crps'].mean())
# st.metric("Humidity", "86%", "4%")

st.header('Probabilistic Verification - Overall Metrics')

######### Lead Time Metrics

col1, col2 = st.columns(2)

with col1:
    # CRPS Plot ##########################################
    trace1 = go.Scatter(x=overall_model_leadtime['lead_hour'],
                        y=overall_model_leadtime['crps'],
                        mode='lines',
                        name=f'{st.session_state["ref_model"]}' )

    trace2 = go.Scatter(x=overall_epd_leadtime['lead_hour'],
                        y=overall_epd_leadtime['crps'],
                        mode='lines',
                        name='ePD' )

    layout = go.Layout(
        title='Mean Continous Ranked Probability Score - All Stations',
        xaxis=dict(title='Lead Time Hour'),
        yaxis=dict(title='Deg C')
    )

    # create plot figure with multiple line plot traces
    fig1 = go.Figure(data=[trace1, trace2], layout=layout)
    fig1.update_xaxes(range=[0 ,st.session_state["max_lead"]])
    st.plotly_chart(fig1,use_container_width=False)




with col2:
    # MAE Plot ##########################################
    trace1 = go.Scatter(x=overall_model_leadtime['lead_hour'],
                        y=overall_model_leadtime['mae'],
                        mode='lines',
                        name=f'{st.session_state["ref_model"]} - mean' )


    trace2 = go.Scatter(x=overall_epd_leadtime['lead_hour'],
                        y=overall_epd_leadtime['mae'],
                        mode='lines',
                        name='ePD - Mean' )

    trace3 = go.Scatter(x=overall_model_leadtime['lead_hour'],
                        y=overall_model_leadtime['nwp_mae'],
                        mode='lines',
                        name='NWP' )

    layout = go.Layout(
        title='MAE - All Stations',
        xaxis=dict(title='Lead Time Hour'),
        yaxis=dict(title='Deg C')
    )

    # create plot figure with multiple line plot traces
    fig2 = go.Figure(data=[trace1, trace2, trace3], layout=layout)
    fig2.update_xaxes(range=[0 ,st.session_state["max_lead"]])
    st.plotly_chart(fig2,use_container_width=False)




# CRPSS ###############################################
col1, col2 = st.columns(2)

with col1:

    # CRPSS Map ###########################
    fig = px.scatter_mapbox(crpss_station, lat="latitude", lon="longitude", color="crpss", hover_data=["wmoId", "name"],
                            color_continuous_scale='balance_r')
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=4,
        # mapbox_center={"lat": 37.7749, "lon": -122.4194}
    )
    fig.update_layout(title=f'Mean CRPSS - All Stations - DRN vs. ePD')
    st.plotly_chart(fig,use_container_width=False)

with col2:
    st.write(crpss_station[['name','crps_epd', f'crps_{st.session_state["ref_model"]}','crpss']]
             .sort_values('crpss', ascending=False))


# CRPSS ###############################################
col1, col2 = st.columns(2)

with col1:

    # CRPSS
    trace1 = go.Scatter(x=crpss_lead.index,
                        y=crpss_lead['crpss'],
                        mode='lines',
                        name=f'{st.session_state["ref_model"]}' )

    layout = go.Layout(
        title=f'Mean CRPSS - All Stations - DRN vs. ePD',
        xaxis=dict(title='Lead Time Hour'),
        yaxis=dict(title='CRPSS')
    )

    # create plot figure with multiple line plot traces
    fig1 = go.Figure(data=[trace1], layout=layout)
    fig1.add_hline(y=0, line_width=2, line_color="red")
    fig1.update_xaxes(range=[0 ,st.session_state["max_lead"]])
    st.plotly_chart(fig1,use_container_width=False)


with col2:

    # CRPSS BOX 
    fig = px.box(crpss_station.reset_index(), #model_prob_bins_stations.index.get_level_values('bin'),
                y='crpss',
                # color="model",
                notched=False, # used notched shape
                title="Box plot of total bill",
                hover_data='stationId' # add day column to hover data
                )
    fig.add_hline(y=0, line_width=2, line_color="red")
    # fig.update_xaxes(range=[-0.05,0.95])
    fig.update_layout(title='Mean CRPSS - Stations Distribution - DRN vs. ePD',
                    yaxis=dict(title='CRPSS'))
    st.plotly_chart(fig,use_container_width=False)




# PIT Histogram ####################################
col1, col2 = st.columns(2)

with col1:

    # PIT Overall
    fig = px.bar(models_prob_bins.reset_index(), x='bin', y='cp_obs_count',color='model',  barmode='group', facet_col=None)
    fig.add_hline(y=0.1, line_width=2, line_color="red")
    fig.update_xaxes(range=[-0.05,0.95])
    fig.update_layout(title='PIT Histogram - Mean All Stations',
                    xaxis=dict(title='Forecast probability Quantile'),
                    yaxis=dict(title='Rate of Observed values'))
    st.plotly_chart(fig,use_container_width=False)

with col2:
    # PIT Distribution
    fig = px.box(model_prob_bins_stations.reset_index(), x='bin', #model_prob_bins_stations.index.get_level_values('bin'),
                y='cp_obs_count',
                color="model",
                notched=False, # used notched shape
                title="Box plot of total bill",
                hover_data='stationId' # add day column to hover data
                )
    fig.add_hline(y=0.1, line_width=2, line_color="red")
    fig.update_xaxes(range=[-0.05,0.95])
    fig.update_layout(title='PIT Histogram - Stations Distribution',
                    xaxis=dict(title='Forecast probability Quantile'),
                    yaxis=dict(title='Rate of Observed values'))
    st.plotly_chart(fig,use_container_width=False)



# Probs Histogram ####################################
col1, col2 = st.columns(2)

with col1:

    # Probs Overall #####################
    fig = px.bar(models_prob_bins.reset_index(), x='bin', y='p_obs_count',color='model',  barmode='group', facet_col=None)
    fig.update_xaxes(range=[-0.05,0.95])
    fig.update_layout(title='Probability of Observed - Mean All Stations',
                    xaxis=dict(title='Forecast probability'),
                    yaxis=dict(title='Rate of Observed values'))
    st.plotly_chart(fig,use_container_width=False)

with col2:
    # PIT Distribution
    fig = px.box(model_prob_bins_stations.reset_index(), x='bin', #model_prob_bins_stations.index.get_level_values('bin'),
                y='p_obs_count',
                color="model",
                notched=False, # used notched shape
                title="Box plot of total bill",
                hover_data='stationId' # add day column to hover data
                )
    fig.update_xaxes(range=[-0.05,0.95])
    fig.update_layout(title='Probability of Observed - Stations Distribution',
                    xaxis=dict(title='Forecast probability'),
                    yaxis=dict(title='Rate of Observed values'))
    st.plotly_chart(fig,use_container_width=False)