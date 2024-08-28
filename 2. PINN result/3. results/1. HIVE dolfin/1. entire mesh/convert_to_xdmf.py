import meshio

# Read the original CGNS or UNV file
mesh = meshio.read("Sample.msh")  # or "original_mesh.unv"

# Write to XDMF
mesh.write("output/fenics_mesh.xdmf")

