import streamlit as st
import pandas as pd
import plotly.express as px





fig = px.scatter_mapbox(st.session_state["stations_attributes"] , lat="latitude", lon="longitude", zoom=3)

fig.update_layout(mapbox_style="carto-positron")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig)