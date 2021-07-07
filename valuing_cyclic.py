# valuing_cyclic.py -----------------------------------------------------------------------------------------
#   Cyclical companies have revenues that go up and down periodically. The expectation is that free cashflows
# will also go up and down periodically. But when we value companies, we assume that the growth will be 
# linear. This code examines how that assumption will affect valuation
# -----------------------------------------------------------------------------------------------------------
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

# Choose parameters related to the free cashflow
sine_period = 10 # years. Period of business cycle
phase = np.pi/4 # radians. Defines where we are now in the cycle
dc_init_value = 800 # million dollars. This is the initial DC value of the sinusoidal cashflow
hidden_growth_rate = 4 # percent. Instead of the DC value of the sinusoid being constant, we allow it to grow - 
                        # which is how it usually is in reality
amplitude = 300 # million dollars. This is the scale factor that is related to how high/low FCFE can go relative to the -
                 # DC value
no_of_years = 40 # years. Total number of years for which to run the simulation

# Simulate a series of free cashflows (FCFE)
angle_step = 2*np.pi/sine_period
FCFE = np.empty(no_of_years+1, dtype=float)
dc_value = dc_init_value
for i in range(no_of_years+1):
    FCFE[i] = dc_value + amplitude*np.sin(i*angle_step + phase)
    dc_value = dc_value*(1+hidden_growth_rate/100)    

# Calculate a straight line equivalent of FCFEs
actual_g = FCFE[1]/FCFE[0] - 1 # No unit. Actual growth rate.
g_eq = actual_g/4
eq_FCFE = np.empty(no_of_years+1, dtype=float)
eq_FCFE[0] = FCFE[0]
for i in range(1, no_of_years+1):
    eq_FCFE[i] = eq_FCFE[i-1]*(1+g_eq)


# Calculate present values
cost_of_capital = 5 # percent
PV = npf.npv(cost_of_capital/100, FCFE[1:])
eq_PV = npf.npv(cost_of_capital/100, eq_FCFE[1:]) 

# Visualisation
fig, ax = plt.subplots()
ax.scatter(list(range(no_of_years+1)), FCFE, color='blue', label='Actual FCFE')
ax.scatter(list(range(no_of_years+1)), eq_FCFE, color='red', label='Projected FCFE')
ax.set_xlabel('years')
ax.set_ylabel('FCFE')
ax.legend()
fig.suptitle('Approximation of cyclical cashflows')

plt.show()
