# price_compiler.py ---------------------------------------------------------------------------
# Description:
#   Compiles the EOD prices of a given security from getBhavCopy software output data into a
# csv file that is common to all securities. The code checks if the compiled data for a secu -
# -ity is already present in the output csv and asks user whether to overwrite or add only new
# data.
# ---------------------------------------------------------------------------------------------

# IMPORTANT INFO
# This code supports only NSE data for now
# TODO: Add BSE support after figuring out a way to convert from security ID to BSE symbol

# Libraries
import math
import numpy as np
import numpy.linalg as la
import pandas as pd
import matplotlib.pyplot as plt

import sys
import os
import errno
from tqdm import tqdm, trange

# Funcitons

# write_compiled_data --------------------------------------------------------
# Takes a data frame, splits it based on a set of values for a certain column
# ----------------------------------------------------------------------------
def write_compiled_data(data, folder, group_by_column_name, group_by_values):
    grouped_data = data.groupby(group_by_column_name)
    for item in group_by_values:
        segregated_data = grouped_data.get_group(item)  # Get data pertaining to one item value
        filename = folder + '/' + item + '.csv'
        if os.path.exists(filename):    # If file already exists, append data
            segregated_data.to_csv(filename, mode='a', index=False, header=False)
        else:                           # Otherwise create a new CSV and store
            segregated_data.to_csv(filename, mode='w', index=False, header=True)
            
         
    
# Default input values
data_source_dir = '/home/dinesh/Documents/security_prices/india'
nse_sub_dir = 'NSE-EOD'
outfolder = data_source_dir + '/' + nse_sub_dir
missing_data_threshold = 5

# MAIN CODE
nse_symbols_str = input('Enter NSE symbol(s) (comma sep if many): ')    # Get one or more stock symbols for which to compile price data
nse_symbols = [strlet.strip() for strlet in nse_symbols_str.split(',')] # 

try:
    nsefiles = os.listdir(data_source_dir + '/' + nse_sub_dir)  # Returns list of files
except Exception as e:
    print('Error: ', e)
    sys.exit(errno.ENOENT)

#if len(nsefiles) == 0:   # Folder is empty. Inform user and exit 
#    print('Error: No files in the raw data folder to process')
#    sys.exit(errno.ENOENT)

compiled_data = pd.DataFrame()
missing_data_count = 0
iteration = 0
for file in tqdm(nsefiles, desc='data read', total=100, leave=True):   # Main loop for compiling data for input symbol
    try:
        filename = data_source_dir + '/' + nse_sub_dir + '/' + file
        data = pd.read_csv(filename, sep=',', na_values='-')
    except Exception as e:
        print('Error: ', e)
        if compiled_data != []: # If we have already iterated a few times and compiled some data
             write_compiled_data(data=compiled_data, folder=outfolder, 
                                 group_by_column_name='<ticker>', group_by_values=nse_symbols)
        sys.exit(errno.EIO)

    if data.empty:
        print('\nError: csv file returned no entries')
        sys.exit(errno.EIO)

    try:
        relevant_data = data[data['<ticker>'].isin(nse_symbols)]    # Extract only data pertaining to the symbols user is - 
    except Exception as e:                                          # interested in
        print('Error: ', e)
        sys.exit(errno.EIO)
    
    if relevant_data.empty: # For the rare case where none of the symbols entered by user exist in the data
        missing_data_count = missing_data_count + 1
        if missing_data_count > missing_data_threshold:
            print('Warning: Too many missing data. Please check entered NSE symbol')
            user_yes_no = input("Continue (y)/ Halt(n)?: ")
            if user_yes_no == 'n':
                sys.exit(errno.EL3HLT)
            else:
                missing_data_count = missing_data_count + 1 
        continue

    iteration = iteration + 1   # Debug code starts here
#    if iteration == 5:      
#        break
#    print(relevant_data)    # Debug code ends here

    compiled_data = compiled_data.append(relevant_data)
    
write_compiled_data(data=compiled_data, folder=outfolder, 
                    group_by_column_name='<ticker>', group_by_values=nse_symbols)

