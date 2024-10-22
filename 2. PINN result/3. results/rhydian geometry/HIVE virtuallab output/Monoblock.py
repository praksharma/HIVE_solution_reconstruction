import sys
import numpy as np
import os
sys.dont_write_bytecode=True
from types import SimpleNamespace
from Scripts.Common.VLFunctions import VerifyParameters

# States the normal direction for each surface
SurfaceNormals = np.array([['TileFront', 'NX'], ['TileBack', 'NX'], ['TileSideA', 'NY'],
                          ['TileSideB', 'NY'], ['TileTop', 'NZ'],
                          ['BlockFront', 'NX'], ['BlockBack', 'NX'], ['BlockSideA', 'NY'],
                          ['BlockSideB', 'NY'],['BlockBottom', 'NZ'], ['BlockTop', 'NZ']])


def Example():
    '''
    Example parameter values.
    '''
    Parameters = SimpleNamespace(Name='Test')
    # === Geometry ===
    Parameters.BlockWidth = 0.03
    Parameters.BlockLength = 0.05
    Parameters.BlockHeight = 0.02

    Parameters.PipeShape = 'smooth tube'

    Parameters.PipeDiam = 0.01 ###Inner Diameter
    Parameters.PipeThick = 0.001
    Parameters.PipeLength = Parameters.BlockLength

    Parameters.TileCentre = [0,0]
    Parameters.TileWidth = Parameters.BlockWidth
    Parameters.TileLength = 0.03
    Parameters.TileHeight = 0.005
    Parameters.PipeCentre = [0,0]

    Parameters.Fillet = 0.00025

    # Parameters.VoidCentre = [[0.25, 0.25],[0.75, 0.75]] # in terms of tile corner
    # Parameters.Void = [[0.001, 0.002, 0.004, 10.0],[0.002, 0.001, 0.004, 0.0]]

    # === Main mesh ===
    Parameters.Length1D = 0.005
    Parameters.Length2D = 0.005
    Parameters.Length3D = 0.005
    # === Pipe sub-mesh ===
    Parameters.PipeSegmentN = 20
    # === Tile sub-mesh ===
    Parameters.SubTile = [0.0008,0.0008,0.001]
    Parameters.CoilFace = 0.0008

    # === Void sub-mesh
    Parameters.VoidSegmentN = 16

    return Parameters

# def Verify(Parameters):
#     ''''
#     Verify that the parameters set in Parameters_Master and/or Parameters_Var
#     are suitable to create the mesh.
#     These can either be a warning or an error
#     '''
#     error, warning = [],[]
#
#     # =============================================================
#     # Check Variables are defined in the parameters
#
#     # Required variables
#     ReqVar = ['Thickness','HandleWidth',
#               'HandleLength','GaugeWidth',
#               'GaugeLength','TransRad',
#               'Length1D','Length2D','Length3D']
#     # Optional variables - all are needed to create a hole
#     OptVar = ['HoleCentre','Rad_a','Rad_b','HoleDisc']

def Create(Parameters):

    from salome.geom import geomBuilder
    from salome.smesh import smeshBuilder
    import  SMESH
    import salome_version
    from Scripts.VLPackages.Salome import SalomeFunc
    import salome

    if salome_version.getVersions()[0] < 9:
        theStudy = salome.myStudy
        geompy = geomBuilder.New(theStudy)
        smesh = smeshBuilder.New(theStudy)
    else :
        geompy = geomBuilder.New()
        smesh = smeshBuilder.New()

    # =========================================================================
    # === GEOM component ======================================================

    O = geompy.MakeVertex(0, 0, 0)
    OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
    OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
    OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)

    geompy.addToStudy( O, 'O' )
    geompy.addToStudy( OX, 'OX' )
    geompy.addToStudy( OY, 'OY' )
    geompy.addToStudy( OZ, 'OZ' )

    ### Creating the sample geometry
    ## Pipe
    InRad = Parameters.PipeDiam/2
    OutRad = Parameters.PipeDiam/2 + Parameters.PipeThick

    Vertex_1 = geompy.MakeVertex(Parameters.BlockWidth/2+Parameters.PipeCentre[0], -0.5*(Parameters.PipeLength-Parameters.BlockLength), Parameters.BlockHeight/2+Parameters.PipeCentre[1])
    Fluid = geompy.MakeCylinder(Vertex_1, OY, InRad, Parameters.PipeLength)
    PipeExt = geompy.MakeCylinder(Vertex_1, OY, OutRad, Parameters.PipeLength)
    Pipe = geompy.MakeCutList(PipeExt, [Fluid], True)
    geompy.addToStudy( Pipe, 'Pipe' )

    ## Block
    Box = geompy.MakeBoxDXDYDZ(Parameters.BlockWidth, Parameters.BlockLength, Parameters.BlockHeight)
    Block = geompy.MakeCutList(Box, [PipeExt], True)
    geompy.addToStudy( Block, 'Block')

    ## Tile
    TileCentre = geompy.MakeVertex(Parameters.BlockWidth/2+Parameters.TileCentre[0], Parameters.BlockLength/2+Parameters.TileCentre[1], Parameters.BlockHeight)
    TileCorner1 = geompy.MakeVertexWithRef(TileCentre, -Parameters.TileWidth/2, -Parameters.TileLength/2, 0)
    TileCorner2 = geompy.MakeVertexWithRef(TileCentre, Parameters.TileWidth/2, Parameters.TileLength/2, Parameters.TileHeight)
    Tile_orig = geompy.MakeBoxTwoPnt(TileCorner1, TileCorner2)

    Tile_orig = geompy.MakeFillet(Tile_orig, Parameters.Fillet, geompy.ShapeType["FACE"], [33])
    geompy.addToStudy( Tile_orig, 'Tile_orig')

    # =============================================================================
    # Add in artificial defects if they exist
    Voids,VoidCentres = getattr(Parameters,'Void',[]),getattr(Parameters,'VoidCentre',[])
    Void_List = []
    for i,(Void,VoidCentre) in enumerate(zip(Voids,VoidCentres)):
        VoidCentreX = Parameters.TileWidth*VoidCentre[0]
        VoidCentreY = (Parameters.BlockLength - Parameters.TileLength)*0.5 + Parameters.TileLength*VoidCentre[1]
        Vertex_2 = geompy.MakeVertexWithRef(O, VoidCentreX, VoidCentreY, Parameters.BlockHeight) # extrusion vector

        VoidGeom = geompy.MakeCylinder(Vertex_2, OZ, max(Void[:2]), Void[2])
        # Scale & (possibly) rotate if it's eliptic
        if Void[0] != Void[1]:
            if Void[0]<Void[1]:
                VoidGeom = geompy.MakeScaleAlongAxes(VoidGeom, Vertex_2, Void[0]/Void[1], 1, 1)
            else:
                VoidGeom = geompy.MakeScaleAlongAxes(VoidGeom, Vertex_2, 1,Void[1]/Void[0], 1)

            if Void[3]:
                Point_1 = geompy.MakeVertex(VoidCentreX, VoidCentreY, 0)
                Point_2 = geompy.MakeVertex(VoidCentreX, VoidCentreY, Parameters.BlockHeight)
                VectorRotation = geompy.MakeVector(Point_1, Point_2)
                VoidGeom = geompy.Rotate(VoidGeom, VectorRotation, Void[3]*np.pi/180.0)

        geompy.addToStudy(VoidGeom, 'Void_{}'.format(i))
        Void_List.append(VoidGeom)

    if Void_List:   # void(s) case
        Tile = geompy.MakeCutList(Tile_orig, Void_List, True)
    else:   # no void case
        Tile = Tile_orig

    # =============================================================================
    # Combine Tile, Block & Pipe
    Fuse = geompy.MakeFuseList([Pipe, Block, Tile], True, True)
    Sample = geompy.MakePartition([Fuse], [Pipe, Block, Tile], [], [], geompy.ShapeType["SOLID"], 0, [], 0)

    geompy.addToStudy(Tile,'Tile')
    geompy.addToStudy(Sample, 'Sample')

    # =============================================================================
    # Create groups on Sample geometry
    '''
    ObjIndex function returns the object index of a sub-shape in a new geometry
    i.e. we want to know what the object index of a sub-shape of the tile is in
    sample to create a group there.
    '''

    # Solid
    Ix = SalomeFunc.ObjIndex(Sample, Tile, [1])[0]
    GrpTile = SalomeFunc.AddGroup(Sample, 'Tile', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [1])[0]
    GrpPipe = SalomeFunc.AddGroup(Sample, 'Pipe', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Block, [1])[0]
    GrpBlock = SalomeFunc.AddGroup(Sample, 'Block', Ix)

    # Surfaces
    Ix = SalomeFunc.ObjIndex(Sample, Tile_orig, [45])[0]
    GrpCoilFace = SalomeFunc.AddGroup(Sample, 'CoilFace', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Tile_orig, [20,40,50,53])[0]
    GrpFillet = SalomeFunc.AddGroup(Sample, 'Fillet', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Tile_orig, [3,13,32,37])[0]
    GrpTileSide= SalomeFunc.AddGroup(Sample, 'TileSide', Ix)

    # Ix = SalomeFunc.ObjIndex(Sample, Tile_orig, [27])[0]
    # GrpTileBase = SalomeFunc.AddGroup(Sample, 'TileBase', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [20])[0]
    GrpPipeFace = SalomeFunc.AddGroup(Sample, 'PipeFace', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [15])[0]
    GrpPipeIn = SalomeFunc.AddGroup(Sample, 'PipeIn', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [10])[0]
    GrpPipeOut = SalomeFunc.AddGroup(Sample, 'PipeOut', Ix)

    # Edges
    Ix = SalomeFunc.ObjIndex(Sample, Tile_orig, [5,12,15,34])[0]
    GrpTileEdge = SalomeFunc.AddGroup(Sample, 'TileEdge', Ix)

    # Vertices
    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [8])[0]
    GrpPipeInV1 = SalomeFunc.AddGroup(Sample, 'PipeInV1', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [19])[0]
    GrpPipeInV2 = SalomeFunc.AddGroup(Sample, 'PipeInV2', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [6])[0]
    GrpPipeOutV1 = SalomeFunc.AddGroup(Sample, 'PipeOutV1', Ix)

    Ix = SalomeFunc.ObjIndex(Sample, Pipe, [14])[0]
    GrpPipeOutV2 = SalomeFunc.AddGroup(Sample, 'PipeOutV2', Ix)

    # Create groups for surfaces of the sample include additional surfaces
    # created when parts join
    # Pipe
    PipeIntIx = SalomeFunc.ObjIndex(Sample, Pipe, [10,15,20])[0]
    # When the pipe is longer than the block
    CutPipBlk = geompy.MakeCutList(geompy.GetSubShape(Pipe,[3]), [geompy.GetSubShape(Block,[41])], True)
    _PipeIx = geompy.SubShapeAllIDs(CutPipBlk, geompy.ShapeType["FACE"])
    if _PipeIx:
        PipeExtIx = SalomeFunc.ObjIndex(Sample, CutPipBlk, _PipeIx)[0]
    else: PipeExtIx = []

    # Block
    BlockExtIx = SalomeFunc.ObjIndex(Sample, Block, [3,13,28,36,39])[0]
    # When the Block is longer/wider than the tile
    CutBlkTl = geompy.MakeCutList(geompy.GetSubShape(Block,[23]), [geompy.GetSubShape(Tile_orig,[27])], True)
    _BlkIx = geompy.SubShapeAllIDs(CutBlkTl, geompy.ShapeType["FACE"])
    if _BlkIx:
        BlockExtIx += SalomeFunc.ObjIndex(Sample, CutBlkTl, _BlkIx)[0]

    # Tile
    TileExtIx = SalomeFunc.ObjIndex(Sample, Tile_orig, [3,13,20,32,37,40,45,50,53])[0]
    # When the tile is longer/wider than the tile
    CutTlBlk = geompy.MakeCutList(geompy.GetSubShape(Tile_orig,[27]), [geompy.GetSubShape(Block,[23])], True)
    _TlIx = geompy.SubShapeAllIDs(CutTlBlk, geompy.ShapeType["FACE"])
    if _TlIx:
        TileExtIx += SalomeFunc.ObjIndex(Sample, CutTlBlk, _TlIx)[0]

    # External surface group 'SampleSurface' for ERMES
    ERMESSurface = TileExtIx + BlockExtIx + PipeExtIx + PipeIntIx
    GrpSampleSurface = SalomeFunc.AddGroup(Sample, 'SampleSurface', ERMESSurface)

    GrpTileExternal = SalomeFunc.AddGroup(Sample, 'TileExternal', TileExtIx)
    GrpBlockExternal = SalomeFunc.AddGroup(Sample, 'BlockExternal', BlockExtIx)


    # Create groups to add virtual thermocouples to
    TC_ID = [['Tile', 'Front', 37], ['Tile', 'Back', 3], ['Tile', 'SideA', 13],
             ['Tile', 'SideB', 32], ['Tile', 'Top', 45],
             ['Block', 'Front', 39], ['Block', 'Back', 3], ['Block', 'SideA', 13],
             ['Block', 'SideB', 28],['Block', 'Bottom', 36]] # TC_ID: ThermoCouple ID

    GrpThermocouple = []
    for Part, Face, Id in TC_ID:
        # Convert ID to Sample specific ID
        if Part == 'Tile': SurfaceID = SalomeFunc.ObjIndex(Sample, Tile_orig, [Id])[0]
        elif Part == 'Block': SurfaceID = SalomeFunc.ObjIndex(Sample, Block, [Id])[0]
        # Create group & keep in list
        grp = SalomeFunc.AddGroup(Sample, Part+Face, SurfaceID)
        GrpThermocouple.append(grp)


    #Create groups for void surfaces for finer meshing
    VoidSurfaces = []
    for i,_Void in enumerate(Void_List):
        Ix = SalomeFunc.ObjIndex(Sample, _Void, [3, 10, 12])[0]
        VoidSurfaces.append(SalomeFunc.AddGroup(Sample,"Void_{}_Surface".format(i), Ix))

    # Get surfaces whcich join the different parts together
    # Tile-Block. need to consider if there are voids in the surface
    if Void_List:
        TB_Surf_Void = geompy.MakeCutList(geompy.GetSubShape(Tile_orig,[27]), Void_List, True)
        TileBlock = geompy.MakeCommonList([geompy.GetSubShape(Block,[23]), TB_Surf_Void], True)
    else:
        TileBlock = geompy.MakeCommonList([geompy.GetSubShape(Block,[23]), geompy.GetSubShape(Tile_orig,[27])], True)
    TileBlockId = geompy.SubShapeAllIDs(TileBlock, geompy.ShapeType["FACE"])
    NewId = SalomeFunc.ObjIndex(Sample, TileBlock, TileBlockId)[0]
    GrpTileBlock = SalomeFunc.AddGroup(Sample, 'TileBlock', NewId)

    # Block-Pipe join
    BlockPipe = geompy.MakeCommonList([geompy.GetSubShape(Pipe,[3]), geompy.GetSubShape(Block,[41])],True)
    BlockPipeId = geompy.SubShapeAllIDs(BlockPipe, geompy.ShapeType["FACE"])
    NewId = SalomeFunc.ObjIndex(Sample, BlockPipe, BlockPipeId)[0]
    GrpBlockPipe = SalomeFunc.AddGroup(Sample, 'BlockPipe', NewId)

    #============================================================================
    ###
    ### SMESH component
    ###

    # Main mesh
    Mesh_1 = smesh.Mesh(Sample)
    Check = Mesh_1.Segment()
    Local_Length = Check.LocalLength(Parameters.Length1D,None,1e-07)

    NETGEN_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D)
    NETGEN_2D_Parameters = NETGEN_2D.Parameters()
    NETGEN_2D_Parameters.SetMaxSize( Parameters.Length2D )
    NETGEN_2D_Parameters.SetOptimize( 1 )
    NETGEN_2D_Parameters.SetFineness( 3 )
    NETGEN_2D_Parameters.SetChordalError( 0.1 )
    NETGEN_2D_Parameters.SetChordalErrorEnabled( 0 )
    NETGEN_2D_Parameters.SetMinSize( 0.5*Parameters.Length2D )
    NETGEN_2D_Parameters.SetUseSurfaceCurvature( 1 )
    NETGEN_2D_Parameters.SetQuadAllowed( 0 )

    NETGEN_3D = Mesh_1.Tetrahedron()
    NETGEN_3D_Parameters = NETGEN_3D.Parameters()
    NETGEN_3D_Parameters.SetMaxSize( Parameters.Length3D )
    NETGEN_3D_Parameters.SetOptimize( 1 )
    NETGEN_3D_Parameters.SetFineness( 3 )
    NETGEN_3D_Parameters.SetMinSize( 0.5*Parameters.Length3D )

    smesh.SetName(Local_Length, 'Local Length')
    smesh.SetName(Check.GetAlgorithm(), 'Check')
    smesh.SetName(NETGEN_2D.GetAlgorithm(), 'NETGEN 2D')
    smesh.SetName(NETGEN_2D_Parameters, 'NETGEN 2D Parameters')
    smesh.SetName(NETGEN_3D.GetAlgorithm(), 'NETGEN 3D')
    smesh.SetName(NETGEN_3D_Parameters, 'NETGEN 3D Parameters')
    smesh.SetName(Mesh_1.GetMesh(), 'Sample')

    #==========================================================================
    # Pipe sub-mesh
    # Length1 = (Parameters.PipeDiam*np.pi/Parameters.PipeSegmentN)*0.75 #?????
    Length1 = (Parameters.PipeDiam*np.pi/Parameters.PipeSegmentN)

    PipeSM_1D = Mesh_1.Segment(geom=GrpPipe)
    PipeSM_1D_Parameters = PipeSM_1D.LocalLength(Length1,None,1e-07)
    PipeSM_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=GrpPipe)
    PipeSM_2D_Parameters = PipeSM_2D.Parameters()
    PipeSM_2D_Parameters.SetMaxSize( Length1 )
    PipeSM_2D_Parameters.SetOptimize( 1 )
    PipeSM_2D_Parameters.SetFineness( 3 )
    PipeSM_2D_Parameters.SetChordalError( 0.1 )
    PipeSM_2D_Parameters.SetChordalErrorEnabled( 0 )
    PipeSM_2D_Parameters.SetMinSize( Length1 )
    PipeSM_2D_Parameters.SetUseSurfaceCurvature( 1 )
    PipeSM_2D_Parameters.SetQuadAllowed( 0 )
    PipeSM_3D = Mesh_1.Tetrahedron(geom=GrpPipe)
    PipeSM_3D_Parameters = PipeSM_3D.Parameters()
    PipeSM_3D_Parameters.SetMaxSize( Length1 )
    PipeSM_3D_Parameters.SetOptimize( 1 )
    PipeSM_3D_Parameters.SetFineness( 3 )
    PipeSM_3D_Parameters.SetMinSize( Length1 )
    PipeSM = PipeSM_1D.GetSubMesh()

    smesh.SetName(PipeSM, 'Pipe')
    smesh.SetName(PipeSM_1D_Parameters, 'PipeSM_1D_Parameters')
    smesh.SetName(PipeSM_2D_Parameters, 'Pipe 2D Parameters')
    smesh.SetName(PipeSM_3D_Parameters, 'Pipe 3D Parameters')

    # Update main mesh parameteres with new minimum sizes
    NETGEN_2D_Parameters.SetMinSize( Length1 )
    NETGEN_3D_Parameters.SetMinSize( Length1 )

    #==========================================================================
    # Tile sub-mesh
    # This is broken down in to many parts

    #==========================================================================
    # Fillet sub-mesh
    # Frac of 1/25 pus about 2 elements over the fillet. Increasing to 1/50 will
    # make 5 elements over the fillet
    frac = getattr(Parameters,'Deflection',1/25)
    deflection = Parameters.Fillet*frac
    minl = frac*Parameters.Fillet*6*11**0.5
    maxl = 2*minl

    FilletSM_1D = Mesh_1.Segment(geom=GrpFillet)
    FilletSM_1D_Parameters = FilletSM_1D.Adaptive(minl, maxl, deflection)
    FilletSM_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=GrpFillet)
    FilletSM_2D_Parameters = FilletSM_2D.Parameters()
    FilletSM_2D_Parameters.SetOptimize( 1 )
    FilletSM_2D_Parameters.SetFineness( 2 )
    FilletSM_2D_Parameters.SetChordalError( 0.01 )
    FilletSM_2D_Parameters.SetChordalErrorEnabled( 0 )
    FilletSM_2D_Parameters.SetUseSurfaceCurvature( 1 )
    FilletSM_2D_Parameters.SetQuadAllowed( 0 )
    FilletSM_2D_Parameters.SetMaxSize( maxl )
    FilletSM_2D_Parameters.SetMinSize( minl )
    FilletSM = FilletSM_1D.GetSubMesh()

    smesh.SetName(FilletSM, 'Fillet')
    smesh.SetName(FilletSM_1D_Parameters, 'FilletSM_1D_Parameters')
    smesh.SetName(FilletSM_2D_Parameters, 'FilletSM_2D_Parameters')

    #==========================================================================
    # Tile Sides
    TileSideSM_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=GrpTileSide)
    TileSideSM_2D_Parameters = TileSideSM_2D.Parameters()
    TileSideSM_2D_Parameters.SetOptimize( 1 )
    TileSideSM_2D_Parameters.SetFineness( 2 )
    TileSideSM_2D_Parameters.SetUseSurfaceCurvature( 1 )
    TileSideSM_2D_Parameters.SetQuadAllowed( 0 )
    TileSideSM_2D_Parameters.SetMaxSize( Parameters.SubTile[1] )
    TileSideSM_2D_Parameters.SetMinSize( minl )
    TileSideSM = TileSideSM_2D.GetSubMesh()

    smesh.SetName(TileSideSM, 'TileSide')
    # smesh.SetName(NETGEN_2D_Parameters_20, 'NETGEN 2D Parameters_20')

    #==========================================================================
    # Tile Top
    CoilFaceDisc = getattr(Parameters,'CoilFace',Parameters.SubTile[1])
    TileTopSM_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=GrpCoilFace)
    TileTopSM_2D_Parameters = TileTopSM_2D.Parameters()
    TileTopSM_2D_Parameters.SetOptimize( 1 )
    TileTopSM_2D_Parameters.SetFineness( 2 )
    TileTopSM_2D_Parameters.SetUseSurfaceCurvature( 1 )
    TileTopSM_2D_Parameters.SetQuadAllowed( 0 )
    TileTopSM_2D_Parameters.SetMaxSize( CoilFaceDisc )
    TileTopSM_2D_Parameters.SetMinSize( minl )
    TileTopSM = TileTopSM_2D.GetSubMesh()

    smesh.SetName(TileTopSM, 'TileTop')
    # smesh.SetName(NETGEN_2D_Parameters_11, 'NETGEN 2D Parameters_11')

    #==========================================================================
    # Tile Edge
    # Going from small to large top to bottom
    # Orientation od edges can change so need to find the ones which require 'reversing'
    Reverse = []
    for e in GrpTileEdge.GetSubShapeIndices():
        b1,b2 = geompy.SubShapeAll(geompy.GetSubShape(Sample,[e]),geompy.ShapeType["VERTEX"])
        cb1,cb2 = geompy.PointCoordinates(b1),geompy.PointCoordinates(b2)
        # if point 1 is less than point 2 in z direction then it needs reversing.
        # this is because edge goes point1 to point2, and we need higher point first.
        if cb1[2]<cb2[2]:Reverse.append(e)

    TileEdgeSM_1D = Mesh_1.Segment(geom=GrpTileEdge)
    TileEdgeSM_1D_Parameters = TileEdgeSM_1D.StartEndLength(minl,Parameters.SubTile[0],Reverse)
    TileEdgeSM = TileEdgeSM_1D.GetSubMesh()

    smesh.SetName(TileEdgeSM, 'TileEdge')
    # smesh.SetName(StartEnd, 'StartEnd')

    #==========================================================================
    # Tile
    Tile_1D = Mesh_1.Segment(geom=GrpTile)
    Tile_1D_Parameters = Tile_1D.LocalLength(Parameters.SubTile[0],None,1e-07)
    Tile_2D = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=GrpTile)
    Tile_2D_Parameters = Tile_2D.Parameters()
    Tile_2D_Parameters.SetOptimize( 1 )
    Tile_2D_Parameters.SetFineness( 3 )
    Tile_2D_Parameters.SetChordalError( 0.01 )
    Tile_2D_Parameters.SetChordalErrorEnabled( 0 )
    Tile_2D_Parameters.SetUseSurfaceCurvature( 1 )
    Tile_2D_Parameters.SetQuadAllowed( 0 )
    Tile_2D_Parameters.SetMaxSize( min(2*CoilFaceDisc,Parameters.Length2D) )
    Tile_2D_Parameters.SetMinSize( minl )
    Tile_3D = Mesh_1.Tetrahedron(geom=GrpTile)
    Tile_3D_Parameters = Tile_3D.Parameters()
    Tile_3D_Parameters.SetOptimize( 1 )
    Tile_3D_Parameters.SetFineness( 3 )
    Tile_3D_Parameters.SetMaxSize( Parameters.SubTile[2] )
    Tile_3D_Parameters.SetMinSize( minl )
    TileSM = Tile_1D.GetSubMesh()

    smesh.SetName(TileSM, 'Tile')
    # smesh.SetName(NETGEN_3D_Parameters_2, 'NETGEN 3D Parameters_4')

    MeshOrder = [FilletSM,TileSideSM,TileTopSM,TileEdgeSM,TileSM]

    #==========================================================================
    # Void sub-mesh
    for i, (VoidSurface,Void) in enumerate(zip(VoidSurfaces,Voids)):
        local_mesh_size = np.pi * ((2*((0.5*min(Void[:2]))**2.0 + (0.5*max(Void[:2]))**2))**0.5)/Parameters.VoidSegmentN
        sc = 0.05

        Regular_1D_3 = Mesh_1.Segment(geom=VoidSurface)
        Local_Length_3 = Regular_1D_3.Adaptive(sc*local_mesh_size, local_mesh_size,0.005)
        NETGEN_2D_3 = Mesh_1.Triangle(algo=smeshBuilder.NETGEN_2D,geom=VoidSurface)
        NETGEN_2D_Parameters_3 = NETGEN_2D_3.Parameters()
        NETGEN_2D_Parameters_3.SetMaxSize( local_mesh_size )
        NETGEN_2D_Parameters_3.SetOptimize( 1 )
        NETGEN_2D_Parameters_3.SetFineness( 3 )
        NETGEN_2D_Parameters_3.SetChordalError( 0.01 )
        NETGEN_2D_Parameters_3.SetChordalErrorEnabled( 0 )
        NETGEN_2D_Parameters_3.SetMinSize(sc*local_mesh_size )
        NETGEN_2D_Parameters_3.SetUseSurfaceCurvature( 1 )
        NETGEN_2D_Parameters_3.SetQuadAllowed( 0 )
        Sub_mesh_3 = NETGEN_2D_3.GetSubMesh()

        smesh.SetName(Sub_mesh_3, 'Void_{}_Mesh'.format(i))
        smesh.SetName(NETGEN_2D_Parameters_3, 'NETGEN 2D Parameters-Void_{}'.format(i))
        #NETGEN_2D_Parameters_2.SetMaxSize( local_mesh_size )
        #NETGEN_3D_Parameters_2.SetMaxSize( local_mesh_size )
        Tile_2D_Parameters.SetMinSize( sc*local_mesh_size )
        Tile_3D_Parameters.SetMinSize( sc*local_mesh_size )

        # Create mesh group for each void surface
        Mesh_Void_Ext = Mesh_1.GroupOnGeom(VoidSurface, VoidSurface.GetName(),SMESH.FACE)

        MeshOrder.insert(0,Sub_mesh_3)

    Mesh_1.SetMeshOrder( [ MeshOrder ])


    ## Add Groups
    # Volume
    MSample = Mesh_1.GroupOnGeom(Sample,'Sample',SMESH.VOLUME)
    MTile = Mesh_1.GroupOnGeom(GrpTile,'Tile',SMESH.VOLUME)
    MPipe = Mesh_1.GroupOnGeom(GrpPipe,'Pipe',SMESH.VOLUME)
    MBlock = Mesh_1.GroupOnGeom(GrpBlock,'Block',SMESH.VOLUME)

    # Face
    MCoilFace = Mesh_1.GroupOnGeom(GrpCoilFace,'CoilFace',SMESH.FACE)
    MPipeFace = Mesh_1.GroupOnGeom(GrpPipeFace,'PipeFace',SMESH.FACE)
    MSampleSurface = Mesh_1.GroupOnGeom(GrpSampleSurface,'SampleSurface',SMESH.FACE)
    MPipeIn = Mesh_1.GroupOnGeom(GrpPipeIn,'PipeIn',SMESH.FACE)
    MPipeOut = Mesh_1.GroupOnGeom(GrpPipeOut,'PipeOut',SMESH.FACE)
    MTileBlock = Mesh_1.GroupOnGeom(GrpTileBlock, 'ContactTB', SMESH.FACE)
    MBlockPipe = Mesh_1.GroupOnGeom(GrpBlockPipe, 'ContactBP', SMESH.FACE)
    MTileExternal = Mesh_1.GroupOnGeom(GrpTileExternal, 'TileExternal', SMESH.FACE)
    MBlockExternal = Mesh_1.GroupOnGeom(GrpBlockExternal, 'BlockExternal', SMESH.FACE)

    # Add the thermocouple faces
    for TCgeom in GrpThermocouple:
        Mesh_1.GroupOnGeom(TCgeom, TCgeom.GetName(), SMESH.FACE)

    # Node
    MPipeInV1 = Mesh_1.GroupOnGeom(GrpPipeInV1,'PipeInV1',SMESH.NODE)
    MPipeInV2 = Mesh_1.GroupOnGeom(GrpPipeInV2,'PipeInV2',SMESH.NODE)
    MPipeOutV1 = Mesh_1.GroupOnGeom(GrpPipeOutV1,'PipeOutV1',SMESH.NODE)
    MPipeOutV2 = Mesh_1.GroupOnGeom(GrpPipeOutV2,'PipeOutV2',SMESH.NODE)
    MPipe = Mesh_1.GroupOnGeom(GrpPipe,'PipeNd',SMESH.NODE)
    MSample = Mesh_1.GroupOnGeom(GrpBlock,'BlockNd',SMESH.NODE)

    isDone = Mesh_1.Compute() # have to compute mesh before duplicating faces

    # Add contact surfaces
    ContactSurfaces = [MTileBlock,MBlockPipe]
    # Elems = []
    for cs in ContactSurfaces:
        Affected = Mesh_1.AffectedElemGroupsInRegion([cs], [], None )
        #Affected sometime include strange elements in faces and edge groups so
        # this removes any that are not in the volumes
        nds = Affected[0].GetNodeIDs()
        for aff in Affected[1:]:
            Cnct = [Mesh_1.GetElemNodes(num) for num in aff.GetIDs()]
            badbl = np.invert(np.all(np.isin(Cnct,nds),axis=1))
            badelem = (np.array(aff.GetIDs())[badbl]).tolist()
            aff.Remove(badelem)
        NewGrps = Mesh_1.DoubleNodeElemGroups( [ cs ], [], Affected, 1, 0 )
        # Elems+=cs.GetIDs() + NewGrps.GetIDs()
        [Mesh_1.RemoveGroup(grp) for grp in Affected]

    # ExtSurf = Mesh_1.CreateEmptyGroup(SMESH.FACE,'CS_External')
    # ExtSurf.Add(MSampleSurface.GetIDs()+Elems)


    globals().update(locals()) ### This adds all variables created in this function

    return Mesh_1

if __name__ == '__main__':
    if len(sys.argv) == 1:
        Create(Example())
    # 1 argument provided which is the parameter file
    elif len(sys.argv) == 2:
        ParameterFile = sys.argv[1]
        sys.path.insert(0, os.path.dirname(ParameterFile))
        Parameters = __import__(os.path.splitext(os.path.basename(ParameterFile))[0])
        Create(Parameters)
