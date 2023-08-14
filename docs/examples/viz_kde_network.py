"""
=======================================================
Visualize Interdisciplinary map of the journals network
=======================================================

The goal of this app is to show an overview of the journals network structure
as a complex network. Each journal is shown as a node and their connections
indicates a citation between two of them.
"""

###############################################################################
# First, let's import some useful functions

from os.path import join as pjoin

import numpy as np

from fury import actor
from fury import colormap as cmap
from fury import window
from fury.actors.effect_manager import EffectManager
from fury.data import fetch_viz_wiki_nw

###############################################################################
# Then let's download some available datasets.


files, folder = fetch_viz_wiki_nw()
categories_file, edges_file, positions_file = sorted(files.keys())

###############################################################################
# We read our datasets

positions = np.loadtxt(pjoin(folder, positions_file))

print(type(positions))

slice = 1000

positions = positions[:slice]
cm = np.average(positions, axis = 0)
print(positions.shape)
print(positions)
print(cm)

radii = 1 + np.random.rand(len(positions))




scene = window.Scene()

# scene.set_camera((-500, -500, -500), cm, (0.0, 0.0, 1.0))


width, height = (1200, 1000)
manager = window.ShowManager(
    scene,
    "demo",
    (width,
     height))

manager.initialize()

em = EffectManager(manager)
kde_actor = em.kde(positions, 5.0, "gaussian", colormap = "inferno")

manager.scene.add(kde_actor)

markers_actor = actor.markers(positions, scales = 3.0)

manager.scene.add(markers_actor)

interactive = True

if interactive:
    manager.start()

window.record(scene, out_path='journal_networks.png', size=(600, 600))
