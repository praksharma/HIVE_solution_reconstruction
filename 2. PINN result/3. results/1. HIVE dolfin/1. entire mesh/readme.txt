use gmsh to covert unv to msh and then use it to convert to xdmf using the python file.

There is some bug with fenics and msh file conversion when using multiple kinds of elements.

I ended up using the data file exported from salome. It contains the nodal coordiantes and the elemetn connectivity.

Me and GPT4 ended up exporting the tetrathedral elements only, because it gives error for mixed elements and i am too lazy to fix it. The xdmf output from dolfin look very good. We can open it in paraview using the first reader.

So, we don't need this python script for meshio conversion.
