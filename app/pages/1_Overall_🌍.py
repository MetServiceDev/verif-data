import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go



model_station_list = st.session_state["model_station_list"]
epd_station_list = st.session_state["epd_station_list"]


overall_model_leadtime = st.session_state["model_leadtimes"].groupby(st.session_state["model_leadtimes"].index).mean()
overall_epd_leadtime = st.session_state["epd_leadtimes"].groupby(st.session_state["epd_leadtimes"].index).mean()

overall_model_station = (st.session_state["model_leadtimes"]
                        .loc[st.session_state["model_leadtimes"].iloc[:st.session_state["max_lead"]].index]
                        .groupby('stationId').mean() )

overall_epd_station = (st.session_state["epd_leadtimes"]
                        .loc[st.session_state["epd_leadtimes"].iloc[:st.session_state["max_lead"]].index]
                        .groupby('stationId').mean() )

# Metrics
# col1, col2, col3 = st.columns(3)
# st.metric("Temperature", overall_model_leadtime['crps'].mean())
# st.metric("Wind", overall_epd_leadtime['crps'].mean())
# st.metric("Humidity", "86%", "4%")

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
        title='Mean CRPS - All Stations',
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





# PIT histogram ###########################
# trace1 = go.Histogram(x=st.session_state["model_c_obs"],
#                       xbins=dict(start=0, end=1, size=0.1),
#                       histnorm='percent',
#                       name='DRN' )

# trace2 = go.Histogram(x=st.session_state["epd_c_obs"],
#                       xbins=dict(start=0, end=1, size=0.1),
#                       histnorm='percent',
#                       name='ePD' )

# hline = go.layout.Shape(
#     type='line',
#     x0=0,
#     y0=10, # y-value where the line should be drawn
#     x1=1,
#     y1=10, # y-value where the line should be drawn
#     line=dict(color='red', width=2)
# )

# # create plot layout
# layout = go.Layout(
#     title='PIT Histogram - DRN vs. ePD',
#     xaxis=dict(title='PIT'),
#     yaxis=dict(title='% of Observed'),
#     shapes=[hline]
# )

# # create plot figure with multiple line plot traces
# fig2 = go.Figure(data=[trace1, trace2], layout=layout)
# st.plotly_chart(fig2,use_container_width=False)



# # BIAS Plot ##########################################
# trace1 = go.Scatter(x=overall_model_leadtime.index,
#                     y=overall_model_leadtime['error'],
#                     mode='lines',
#                     name='DRN' )

# trace2 = go.Scatter(x=overall_epd_leadtime.index,
#                     y=overall_epd_leadtime['error'],
#                     mode='lines',
#                     name='ePD' )

# trace3 = go.Scatter(x=overall_model_leadtime.index,
#                     y=overall_model_leadtime['nwp_error'],
#                     mode='lines',
#                     name='NWP_MAE' )


# # create plot layout
# layout = go.Layout(
#     title='Time Serie - DRN vs. ePD - Mean +/- SD ',
#     xaxis=dict(title='Valid Time'),
#     yaxis=dict(title='')
# )

# # create plot figure with multiple line plot traces
# fig3 = go.Figure(data=[trace1, trace2, trace3], layout=layout)
# #fig3.update_xaxes(range=[drn_station_basetime['validtime'].min(), drn_station_basetime['validtime'].max()])
# st.plotly_chart(fig3,use_container_width=False)





# fig = px.scatter_mapbox(st.session_state["stations_attributes"] , lat="latitude", lon="longitude", zoom=3)

# fig.update_layout(mapbox_style="carto-positron")
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# st.plotly_chart(fig)