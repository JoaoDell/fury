import numpy as np

from fury.actors.effect_manager import EffectManager
from fury.window import Scene, ShowManager, record

width, height = (1200, 1000)

scene = Scene()
scene.set_camera(position=(-24, 20, -40),
                 focal_point=(0.0,
                              0.0,
                              0.0),
                 view_up=(0.0, 0.0, 1.0))

manager = ShowManager(
    scene,
    "demo",
    (width,
     height))

manager.initialize()


n_points = 1000
points = np.random.rand(n_points, 3)
points = normalize(points, -5, 5)
offset = np.array([0.0, 0.0, 0.0])
points = points + np.tile(offset, points.shape[0]).reshape(points.shape)

sigmas = normalize(np.random.rand(n_points, 1), 0.05, 0.2)

effects = EffectManager(manager)


kde_actor = effects.kde(points, sigmas, kernel="gaussian", colormap="inferno")

manager.scene.add(kde_actor)

interactive = True

if interactive:
    manager.start()

record(scene, out_path="kde_points.png", size=(800, 800))
