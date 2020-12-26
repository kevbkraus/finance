
import math
import numpy as np
import pandas as pd
from pprint import pprint

import sys
import argparse

msg = "General purpose scratch pad"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-n', '--min_num_count', type=int, help='How many min correlation values to find. Default 10')

args = parser.parse_args()

if args.min_num_count:
    min_num_count = args.min_num_count
else:
    min_num_count = 10

consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
risk_return_filename = consolidated_prices_folder + '/risk_return.csv'
corr_mat_filename = consolidated_prices_folder + '/corr_mat.csv'
corr_strength_filename = consolidated_prices_folder + '/corr_strength.csv' 

corr_df = pd.read_csv(corr_mat_filename, index_col=0)

## Find stock pairs that give n min correlation coefficient values
#corr_array = corr_df.values
#bcorr_array = corr_array[~np.isnan(corr_array)] # Drop nan values
#bcorr_array = np.unique(bcorr_array)
#bcorr_array.sort()
#
#for i in range(0,min_num_count): # For the min n correlation values, find security combos
#    s = pd.Series(map(lambda x:list(corr_df.index[corr_df[x] == bcorr_array[i]]), corr_df.columns), index=corr_df.columns)   
#    s.drop(s.index[s.str.len() == 0], inplace=True)
#    print("correlation coeff: ", bcorr_array[i])
#    pprint(s)   

# Efficient way to find stock pairs that give n min correlation coefficient values  
min_s = corr_df.min(skipna=True)    # Results in a series that contains, as its index, the columns of corr_df and
                                    # its values as the min value in the corresponding column of corr_df
min_s.sort_values(inplace=True)     # Sort in ascending order from min value to max value
stock_tuples = list(map(lambda x: (min_s.index[x], corr_df.index[corr_df[min_s.index[x]] == min_s[x]][0]), range(0,2*min_num_count)))   # The reason - 
                                    # for doubling min_num_count is that after we drop duplicates, we may end up with min_num_count
temp_set = set()
temp_useless_obj = [temp_set.add((a,b)) for (a,b) in stock_tuples if (b,a) not in temp_set]
stock_tuples_unique = list(temp_set)
pprint(stock_tuples_unique)
