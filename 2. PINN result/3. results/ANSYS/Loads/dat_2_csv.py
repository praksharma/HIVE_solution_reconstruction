import pandas as pd
df = pd.read_csv('HeatTransfer.dat', sep='\s')
df.to_csv('HeatTransfer.csv', index=None)