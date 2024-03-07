# IRRProbles.py
# Author: Dinesh Thogulua
# Description: Demonstrates situations where IRR misleads us into making the wrong investment decisions

import numpy as np

# Parabola cutting X-axis in two places resulting to two IRRs
cash_flows = [100E6, -300E6, 230E6]
rates = list(range(0,len(cash_flows),1))
rates = np.linspace(0,1,1000)
npv = np.zeros(1000)
npv = [cash_flows/np.power(rate,years) for rate in rates]
discounts = np.power()
