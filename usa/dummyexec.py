import sys
sys.argv =  ['dcf', 'MSFT', '--industry', 'Software (System & Application)']

try:
  exec(open('dcf_valuation.py').read())
except SystemExit:
  print("sys.exit was called")
