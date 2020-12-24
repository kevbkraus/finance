# portfolio_gen.py -------------------------------------------------------------------------------------
#   Generates portfolios comprising of one stock from each GICS sector in a randomized fasjion using
# the following algorithm
#   1. Shortlist SP500 stocks using a criteria
#   2. Seelect a sector at random
#   3. Find the stock with the best return per risk stock in that sector that hasn't been already chosen
#   4. Select at random one among remaining sectors, find the stock that has the least correlation with
#      already chosen and add to it and create a portfolio
#   5. Continue step 4 until all sectors have been exhausted. Save the portfolio
#   6. Repeat steps 1 to 5 as many times as needed
# ------------------------------------------------------------------------------------------------------

import requests
import json
import numpy as np
import pandas as pd

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Filter stocks based on a criteria
# Filter 1: Low P/B value
yinfo_filename = '/home/dinesh/Documents/security_prices/usa/yinfo.csv'
stock_ratios = pd.read_csv(yinfo_filename)
median_PB = stock_ratios['priceToBook'].median()
symbols_shortlist = stock_ratios[stock_ratios['priceToBook'] < median_PB]['symbol'] 


