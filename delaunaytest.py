#!/usr/bin/python
#
# Demonstration of how to plot a triangulated surface.
#
# We randomly tesselate the (x,y) plane and compute two quadratic functions
# over those points.  The plot displays the two surfaces, each coloured by the
# average z-location of the triangle.
#
import random as rn
import numpy  as np

# Matplot lib and its associated toolkits
import matplotlib.delaunay         as dl
import mpl_toolkits.mplot3d.art3d  as ar3
import mpl_toolkits.mplot3d.axes3d as ax3
import matplotlib.pyplot           as plt

# Generate 200 random points between -2.0 and 2.0.
x = np.empty( [ 204 ] )
y = np.empty( [ 204 ] )

x[0:200] = np.random.uniform( -2.0, 2.0, [200] )
y[0:200] = np.random.uniform( -2.0, 2.0, [200] )

# Put corners on the range for interest
x[200:204] = [ -2.0,-2.0,  2.0, 2.0 ]
y[200:204] = [ -2.0,-2.0,  2.0, 2.0 ]

# Create a triangulation of our region.  We will re-use this for both curves.
circumcenters, edges, tri_points, tri_neighbors = dl.delaunay(x, y)

# Compute the first function of (x,y)
z  = 2.0 - 1.0 * ( x[:]**2 + y[:]**2 ) - 0.5*y[:]

# Construct the triangles for the surface.
verts = ( [ np.array( [ [ x[ t[0] ] , y[ t[0] ] , z[ t[0] ] ]
                      , [ x[ t[1] ] , y[ t[1] ] , z[ t[1] ] ]
                      , [ x[ t[2] ] , y[ t[2] ] , z[ t[2] ] ] ] )
            for t in tri_points
          ]
        )

# To get a coloured plot, we need to assign a value to each face that dictates
# the colour.  In this case we'll just use the average z co-ordinate of the
# three triangle vertices.  One of these values is required for each face
# (triangle).
z_color = np.array( [ ( np.sum( v_p[:,2] ) / 3.0 ) for v_p in verts ] )

# Choiced for colour maps are :
#   autumn bone cool copper flag gray hot hsv jet pink prism spring summer
#   winter spectral
cmhot = plt.cm.get_cmap("hot")

# Our triangles are now turned into a collection of polygons using the vertex
# array.  We assign the colour map here, which will figure out its required
# ranges all by itself.
triCol = ar3.Poly3DCollection( verts, cmap=cmhot )

# Set the value array associated with the polygons.
triCol.set_array    ( z_color )

# Let's repeat the process for a second function.
z2 = 2.0 + 1.0 * ( x[:]**2 + y[:]**2 ) - 0.5*y[:]

# Construct the vertices, this time re-using the triangulation but using a new
# z co-ordinate.
verts2 = ( [ np.array( [ [ x[ t[0] ] , y[ t[0] ] , z2[ t[0] ] ]
                       , [ x[ t[1] ] , y[ t[1] ] , z2[ t[1] ] ]
                       , [ x[ t[2] ] , y[ t[2] ] , z2[ t[2] ] ] ] )
            for t in tri_points
          ]
        )

# We require a new array of values that will tell our colour map what to do.
z2_color = np.array( [ ( np.sum( v_p[:,2] ) / 3.0 ) for v_p in verts ] )

# Let's choose a different colour map this time.
cmjet = plt.cm.get_cmap("jet")

# We need a new set of 3D polygons, since this is a new surface.
triCol2 = ar3.Poly3DCollection( verts2, cmap=cmjet )
# Let's set the edge colour to black and make the triangle edges into thicker,
# dashed lines.  Then we assign the array of values that will be used to colour
# the surface.
triCol2.set_edgecolor('k')
triCol2.set_linewidth( 2.0 )
triCol2.set_linestyle( 'dashed' )
triCol2.set_array( z2_color )

# Create the plotting figure and the 3D axes.
fig = plt.figure()
ax = ax3.Axes3D(fig)

# Add our two collections of 3D polygons directly.  The collections have all of
# the point and color information.  We don't need the add_collection3d method,
# since that method actually converts 2D polygons to 3D polygons.  We already
# have 3D polygons.
ax.add_collection( triCol )
ax.add_collection( triCol2 )

# Add a label, for interest
ax.text3D( 0.0, 0.0, 2.1, "Peak/Trough" )

# If we don't bound the axes correctly the display will be off.
ax.set_xlim3d(-2, 2)
ax.set_ylim3d(-2, 2)
ax.set_zlim3d( np.min(z), np.max(z2) )

# We could also print to a file here.
plt.show()
