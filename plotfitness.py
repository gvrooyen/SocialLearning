from matplotlib.pylab import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import art3d

import numpy as np
import matplotlib.delaunay as dl

import pymongo

connection = pymongo.Connection() 
db = connection.SocialLearning
dbc = db.fitness

filter = {'param_mode_spatial': False, 
          'param_mode_cumulative': False, 
          'param_mode_model_bias': False, 
          'param_N_observe': 5, 
          'agent_name': 'Reference.py'}

P_copyFail = []
P_c = []
fitness = []

for sample in dbc.find(filter):
    P_copyFail.append(sample['param_P_copyFail'])
    P_c.append(sample['param_P_c'])
    fitness.append(sample['fitness'])

#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
#
#ax.scatter3D(P_copyFail, P_c, fitness, s=5)
#
#ax.set_xlabel('P_copyFail')
#ax.set_ylabel('P_c')
#ax.set_zlabel('fitness')

circumcenters, edges, tri_points, tri_neighbors = dl.delaunay(P_copyFail, P_c)

# Construct the triangles for the surface.
verts = ( [ np.array( [ [ P_copyFail[ t[0] ] , P_c[ t[0] ] , fitness[ t[0] ] ]
                      , [ P_copyFail[ t[1] ] , P_c[ t[1] ] , fitness[ t[1] ] ]
                      , [ P_copyFail[ t[2] ] , P_c[ t[2] ] , fitness[ t[2] ] ] ] )
            for t in tri_points
          ]
        )
# To get a coloured plot, we need to assign a value to each face that dictates
# the colour.  In this case we'll just use the average z co-ordinate of the
# three triangle vertices.  One of these values is required for each face
# (triangle).
z_color = np.array( [ ( np.sum( v_p[:,2] ) / 5000.0 ) for v_p in verts ] )

# Choiced for colour maps are :
#   autumn bone cool copper flag gray hot hsv jet pink prism spring summer
#   winter spectral
cmhot = plt.cm.get_cmap("hot")

# Our triangles are now turned into a collection of polygons using the vertex
# array.  We assign the colour map here, which will figure out its required
# ranges all by itself.
triCol = art3d.Poly3DCollection( verts, cmap=cmhot )

triCol  .set_edgecolor('k')
triCol.set_linewidth( 1.0 )

# Set the value array associated with the polygons.
triCol.set_array(z_color)

# Create the plotting figure and the 3D axes.
fig = plt.figure()
ax = Axes3D(fig)

# Add our two collections of 3D polygons directly.  The collections have all of
# the point and color information.  We don't need the add_collection3d method,
# since that method actually converts 2D polygons to 3D polygons.  We already
# have 3D polygons.
ax.add_collection(triCol)

ax.set_xlim3d(np.min(P_copyFail), np.max(P_copyFail))
ax.set_ylim3d(np.min(P_c), np.max(P_c))
ax.set_zlim3d( np.min(fitness), np.max(fitness) )

ax.set_xlabel('P_copyFail')
ax.set_ylabel('P_c')
ax.set_zlabel('fitness')

plt.show()
