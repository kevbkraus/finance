# excess_return_indifference.py -------------------------------------------------------------------------
# Derives an indifference curve between an asset's volatility and demanded return. It is assumed that the
# asset's payoff is a normally distributed random variable. 
# -------------------------------------------------------------------------------------------------------

# Import libraries
import math
import numpy as np
from scipy.stats import norm 

import sys
import errno

# Parameters
price = 100 # dollars. The price we are willing to pay for an asset
r_f = 0.02  # Risk free return. x => x*100 %
confidence_level = 0.95     # Confidence level of not losing below a target level. x => x*100 %
expected_payoff_steps = 10  # No units. No. of samples of expected payoffs for which we want to find volatility 
confidence_level_error = 0.02   # The absolute error level at which we stop the numerical algorithm for 
                                # detecting sigma values

# Derived parameters
target_min_payoff = price*(1+r_f)   # dollars. We will never think of investing in an asset below this value
max_expected_payoff = 2*target_min_payoff   # dollars. Max expected payoff for which we want to find volatility

# Main part of the code begins here
mean_vec = np.linspace(max_expected_payoff, target_min_payoff*1.1, expected_payoff_steps)
sigma_vec = [None] * expected_payoff_steps 
for mean_idx, mean_payoff in enumerate(mean_vec): # We are going to use bisection method
    sigma_a = 1 # dollars. For bisection method to work, we need two x points, a, b, such that, f(a) is +ve and
                # f(b) is -ve
    sigma_b = (mean_payoff - target_min_payoff) * 4
    prob_excess_target_a = 1 - norm(mean_payoff, sigma_a).cdf(target_min_payoff)
    prob_excess_target_b = 1 - norm(mean_payoff, sigma_b).cdf(target_min_payoff)
    objective_fn_a = prob_excess_target_a - confidence_level
    objective_fn_b = prob_excess_target_b - confidence_level
    if (objective_fn_a < 0 and objective_fn_b > 0):
        print('Initial conditions for bisection method aren not satisfied. Quitting')
        sys.exit(errno,EIO)

    sigma_c = (sigma_a + sigma_b)/2 
    prob_excess_target_c = 1 - norm(mean_payoff, sigma_c).cdf(target_min_payoff)
    objective_fn_c = prob_excess_target_c - confidence_level

    iteration_counter = 0
    while abs(objective_fn_c) > confidence_level_error:
        if (objective_fn_c > 0):
            sigma_a = sigma_c
        else: 
            sigma_b = sigma_c
            
        sigma_c = (sigma_a + sigma_b)/2
        prob_excess_target_c = 1 - norm(mean_payoff, sigma_c).cdf(target_min_payoff)
        objective_fn_c = prob_excess_target_c - confidence_level

        iteration_counter = iteration_counter + 1
        if iteration_counter > 100: # This is just a safety mechanism to avoid infinite loops. Newton's method is
                                    # expected to converge really fast
            print("Possible infinte loop detected. Please review code")
            
            sys.exit(errno.ENOEXEC)
    
    print('iteration counter: ', iteration_counter)
    sigma_vec[mean_idx] = sigma_c

# Visualization
