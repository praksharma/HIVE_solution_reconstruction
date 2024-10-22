Name = 'Examples/HIVE_all_copper'
Mesh = 'AMAZE'
Materials = {'Block': 'Copper', 'Pipe': 'Copper', 'Tile': 'Copper'}
Pipe = {'Type': 'smooth tube', 'Diameter': 0.01, 'Length': 0.05}
Coolant = {'Temperature': 30, 'Pressure': 1, 'Velocity': 10}
CoilType = 'HIVE'
CoilDisplacement = [0, 0, 0.0015]
Frequency = 10000.0
AsterFile = 'Monoblock_Steady_nonlinear_solver'
Model = '3D'
Solver = 'MUMPS'
Current = 1000
NbClusters = 100
