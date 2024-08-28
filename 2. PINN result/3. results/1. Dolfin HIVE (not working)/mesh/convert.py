import meshio

# Read the MED mesh
msh = meshio.read("AMAZE.med")

# Direct conversion of mesh is not possible as FEniCS does not support “mixed” mesh composing from several element types before converting to XDMF you’d need to “prune” all lower-dimensional elements
# https://fenicsproject.discourse.group/t/transitioning-from-mesh-xml-to-mesh-xdmf-from-dolfin-convert-to-meshio/412/2?u=prakhar_sharma
# 

# Extract cells of a specific type, e.g., tetrahedral for volume, and triangular for surface
cells_vol = msh.get_cells_type("tetra")
cells_surf = msh.get_cells_type("triangle")

# Prepare cell data for writing, if available
if "tetra" in msh.cell_data:
    cell_data_vol = msh.cell_data_dict["tetra"]
else:
    cell_data_vol = None

if "triangle" in msh.cell_data:
    cell_data_surf = msh.cell_data_dict["triangle"]
else:
    cell_data_surf = None

# Write the volume mesh (3D) to XDMF
meshio.write("mesh.xdmf", meshio.Mesh(points=msh.points, cells={"tetra": cells_vol}, cell_data=cell_data_vol))

# Write the surface mesh (2D) to XDMF, with associated cell data
meshio.write("mf.xdmf", meshio.Mesh(points=msh.points, cells={"triangle": cells_surf}, cell_data=cell_data_surf))



