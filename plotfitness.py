# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
plotfitness.surfplot draws a 3D plot of an agent's fitness function.
"""

from matplotlib.pylab import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import art3d

import numpy as np
import matplotlib.delaunay as dl

import pymongo

global axes

def surfplot(dbc, agent_name, filter, colormap = 'hot'):

    global axes

    P_copyFail = []
    P_c = []
    fitness = []

    # We should only include samples from the database using the latest commit of Simulate.py, and using the latest
    # commit of the agent script being plotted. First, find the latest entry of this agent script, and note the
    # hashes.

    sample = dbc.find({'agent_name': filter['agent_name']}, sort = [('timestamp', -1)], limit = 1).next()
    filter['agent_hash'] = sample['agent_hash']
    filter['simulate_hash'] = sample['simulate_hash']
    
    for sample in dbc.find(filter):
        P_copyFail.append(sample['param_P_copyFail'])
        P_c.append(sample['param_P_c'])
        fitness.append(sample['fitness'])

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
    cm = plt.cm.get_cmap(colormap)
    
    # Our triangles are now turned into a collection of polygons using the vertex
    # array.  We assign the colour map here, which will figure out its required
    # ranges all by itself.
    triCol = art3d.Poly3DCollection( verts, cmap=cm )
    
    triCol.set_edgecolor('k')
    triCol.set_linewidth( 1.0 )
    
    # Set the value array associated with the polygons.
    triCol.set_array(z_color)

    # Add our two collections of 3D polygons directly.  The collections have all of
    # the point and color information.  We don't need the add_collection3d method,
    # since that method actually converts 2D polygons to 3D polygons.  We already
    # have 3D polygons.
    axes.add_collection(triCol)
    
    if axes.get_xlabel() == '':
        xvals = P_copyFail
        yvals = P_c
        zvals = fitness
    #else:   
        #xvals = concatenate((axes.get_xlim3d(), P_copyFail))
        #yvals = concatenate((axes.get_ylim3d(), P_c))
        #zvals = concatenate((axes.get_ylim3d(), fitness))
    
    axes.set_xlim3d(np.min(xvals), np.max(xvals))
    axes.set_ylim3d(np.min(yvals), np.max(yvals))
    axes.set_zlim3d(0, np.max([np.max(zvals), 1500.0]))
    
    axes.set_xlabel('P_copyFail')
    axes.set_ylabel('P_c')
    axes.set_zlabel('fitness')


if __name__ == '__main__':

    global axes
    
    connection = pymongo.Connection() 
    db = connection.SocialLearning
    # db.authenticate('', '')
    dbc = db.fitness
    
    # Create the plotting figure and the 3D axes.
    fig = plt.figure()
    axes = Axes3D(fig)
    
    filter = {'param_mode_spatial': False, 
              'param_mode_cumulative': False, 
              'param_mode_model_bias': False, 
              'param_N_observe': 5, 
              'agent_name': 'Reference.py'}
              
    surfplot(dbc, 'Reference.py', filter, 'hot')
    
    filter = {'param_mode_spatial': False, 
              'param_mode_cumulative': False, 
              'param_mode_model_bias': True, 
              'param_N_observe': 5, 
              'agent_name': 'Reference.py'}
    
    surfplot(dbc, 'Reference.py', filter, 'cool')
    
    plt.show()
