import pandas as pd

# Read the data from the file
data = pd.read_csv('HeatTransfer.dat',sep=' ',header=None)

# Write the data to a CSV file
data.to_csv('Load_CSV/HeatTransfer.csv',index=False,header=False)