import streamlit as st

st.markdown('''
## Continuous Ranked Probability Score (CRPS)

The Continuous Ranked Probability Score (CRPS) is a scoring rule used to evaluate the performance of probabilistic forecast systems.

It measures the distance between the cumulative distribution function (CDF) of the forecast and the observed CDF.

The lower the CRPS value, the better the forecast system's performance. The formula for CRPS is:

$CRPS = \int_{-\infty}^{\infty} [F(y) - H(y)]^2 dy$


where `F(y)` is the CDF of the forecast and `H(y)` is the CDF of the observed values.

The CRPS is expressed in the same unit as the observed variable. 
It generalizes the Mean Absolute Error (MAE), and reduces to the MAE if the forecast is determinstic.

''')
            
st.image('./img/CRPS.PNG')

st.markdown('''
## Continuous Ranked Probability Skill Score (CRPSS)

The Continuous Ranked Probability Skill Score (CRPSS) is a measure of the relative improvement of a forecast system over a reference forecast. 

It is defined as the difference between the CRPS of the forecast system and the CRPS of the reference forecast, divided by the CRPS of the perfect forecast (i.e., the minimum possible CRPS value). 

The formula for CRPSS is:


$CRPSS = 1 - (CRPS_f / CRPS_r)$

where `CRPS_f` is the CRPS of the forecast system, `CRPS_r` is the CRPS of the reference forecast, and `1` is the maximum possible value for the skill score.

CRPSS ranges from `-∞` to `1`, with a value of `1` indicating a perfect forecast system, and a value of `0` indicating a forecast system that is no better than the reference forecast.


'''
)