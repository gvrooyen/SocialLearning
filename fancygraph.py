# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Draw a pretty graph of a given state graph for an agent.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import numpy as np
import networkx as nx
import random

def draw_network(graph,sg=None):

    G = nx.from_agraph(graph)
    pos=nx.spring_layout(G)
    ax=plt.gca()
    ax.set_xmargin(0.25)
    ax.set_ymargin(0.25)
    ax.autoscale()
    plt.axis('equal')
    plt.axis('off')

    for n in G:
        c=Circle(pos[n],radius=0.05,alpha=0.5)
        ax.add_patch(c)
        ax.text(pos[n][0]+0.15, pos[n][1], n, verticalalignment='center')
        G.node[n]['patch']=c
        x,y=pos[n]
    seen={}
    for (u,v,d) in G.edges(data=True):
        n1=G.node[u]['patch']
        n2=G.node[v]['patch']
        rad=random.random()
        if (u,v) in seen:
            rad=seen.get((u,v))
            rad=(rad+np.sign(rad)*0.1)*-1
        alpha=0.5
        color='k'

        e = FancyArrowPatch(n1.center,n2.center,patchA=n1,patchB=n2,
                            arrowstyle='-|>',
                            connectionstyle='arc3,rad=%s'%rad,
                            mutation_scale=10.0,
                            lw=2,
                            alpha=alpha,
                            color=color)
        seen[(u,v)]=rad
        ax.add_patch(e)

