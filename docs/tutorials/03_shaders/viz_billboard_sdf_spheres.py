"""
===============================================================================
SDF Impostors on Billboards
===============================================================================

Traditional rendering engines discretize surfaces using triangles or
quadrilateral polygons. The visual quality of these elements depends on the
amount of the aforementioned polygons used to build the 3D mesh, i.e., a
smoother surface will require more polygons. However, increasing the amount of
rendered polygons comes at the cost of performance as it decreases the number
of frames per second (FPS) which might compromise the real-time interactivity
of a visualization.

Billboarding is a technique that changes an object's orientation so that it
always faces a specific direction, in most cases the camera. This technique
became popular in games and applications that have a high polygonal quota
requirement.

Signed Distance Functions (SDFs) are mathematical functions that describe sets
in a metric space.

This tutorial, exemplifies why FURY's billboard actor is a suitable option when
and how it can be used to create impostors using SDFs.

Let's start by importing the necessary modules:
"""

from fury import actor, window
from fury.shaders import compose_shader, import_fury_shader

import numpy as np
import os

###############################################################################
# Now set up a new scene to place our actors in.
scene = window.Scene()

###############################################################################
# Then define some properties of our actors, use them to create a set of
# spheres, and add them to the scene.
centers = np.array([[0, 0, 0], [-6, -6, -6], [8, 8, 8], [8.5, 9.5, 9.5],
                    [10, -10, 10], [-13, 13, -13], [-17, -17, 17]])
colors = np.array([[1, 1, 0], [1, 0, 1], [0, 0, 1], [1, 1, 1], [1, 0, 0],
                   [0, 1, 0], [0, 1, 1]])
scales = np.array([6, 1.2, 1, .2, .7, 3, 2])
spheres_actor = actor.sphere(centers, colors, radii=scales, phi=8, theta=8,
                             use_primitive=False)
scene.add(spheres_actor)

###############################################################################
# Let's visualize the recently created actors. The following variable can be
# set to **True** to launch an interactive window.
interactive = False

###############################################################################
if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_regular_spheres.png')

###############################################################################
spheres_actor.GetProperty().SetRepresentationToWireframe()

###############################################################################
if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_low_res_wireframe.png')

###############################################################################
scene.clear()
spheres_actor = actor.sphere(centers, colors, radii=scales, phi=16, theta=16,
                             use_primitive=False)
spheres_actor.GetProperty().SetRepresentationToWireframe()
scene.add(spheres_actor)

if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_hi_res_wireframe.png')

###############################################################################
scene.clear()
billboards_actor = actor.billboard(centers, colors=colors, scales=scales)
billboards_actor.GetProperty().SetRepresentationToWireframe()
scene.add(billboards_actor)

###############################################################################
if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_billboards_wireframe.png')

###############################################################################
scene.clear()

###############################################################################
sd_sphere = import_fury_shader(os.path.join('sdf', 'sd_sphere.frag'))

###############################################################################
sphere_radius = 'float sphereRadius = 1;'

###############################################################################
sdf_impl = \
"""
if (sdSphere(point, sphereRadius) < 0)
    fragOutput0 = vec4(color, opacity);
else
    discard;
"""

###############################################################################
fs_impl = compose_shader([sphere_radius, sdf_impl])

###############################################################################
spheres_actor = actor.billboard(centers, colors=colors, scales=scales,
                                fs_dec=sd_sphere, fs_impl=fs_impl)
scene.add(spheres_actor)

###############################################################################
if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_billboards_circles.png')

###############################################################################
scene.clear()

###############################################################################
central_diffs_normal = import_fury_shader(os.path.join('sdf',
                                                       'central_diffs.frag'))

###############################################################################
sd_sphere_normal = \
"""
float map(vec3 p)
{
    return sdSphere(p, 1);
}
"""

###############################################################################
fs_dec = compose_shader([sd_sphere, sd_sphere_normal, central_diffs_normal])

###############################################################################
illum_impl = \
"""
// SDF evaluation
float dist = sdSphere(point, sphereRadius);

if (dist > 0)
    discard;

// Absolute value of the distance
float absDist = abs(dist);

// Normal of a point on the surface of the sphere
vec3 normal = centralDiffsNormals(vec3(point.xy, absDist), .0001);

// Calculate the diffuse factor and diffuse color
df = max(0, normal.z);
diffuse = df * diffuseColor * lightColor0;

// Calculate the specular factor and specular color
sf = pow(df, specularPower);
specular = sf * specularColor * lightColor0;

// Using Blinn-Phong model
fragOutput0 = vec4(ambientColor + diffuse + specular, opacity);
"""

###############################################################################
fs_impl = compose_shader([sphere_radius, illum_impl])

###############################################################################
spheres_actor = actor.billboard(centers, colors=colors, scales=scales,
                                fs_dec=fs_dec, fs_impl=fs_impl)
scene.add(spheres_actor)

###############################################################################
if interactive:
    window.show(scene)

window.record(scene, size=(600, 600), out_path='viz_billboards_spheres.png')
