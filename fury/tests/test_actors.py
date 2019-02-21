import os
import numpy as np

from fury import actor, window
import numpy.testing as npt
from fury.tmpdirs import InTemporaryDirectory
from fury.decorators import xvfb_it
from tempfile import mkstemp
import random
import math
# Allow import, but disable doctests if we don't have dipy
from fury.optpkg import optional_package
dipy, have_dipy, _ = optional_package('dipy')

if have_dipy:
    from dipy.tracking.streamline import (center_streamlines,
                                          transform_streamlines)
    from dipy.align.tests.test_streamlinear import fornix_streamlines
    from dipy.reconst.dti import color_fa, fractional_anisotropy
    from dipy.data import get_sphere

use_xvfb = os.environ.get('TEST_WITH_XVFB', False)
skip_it = use_xvfb == 'skip'


@npt.dec.skipif(skip_it)
@xvfb_it
def test_slicer():
    renderer = window.renderer()
    data = (255 * np.random.rand(50, 50, 50))
    affine = np.eye(4)
    slicer = actor.slicer(data, affine)
    slicer.display(None, None, 25)
    renderer.add(slicer)

    renderer.reset_camera()
    renderer.reset_clipping_range()
    # window.show(renderer)

    # copy pixels in numpy array directly
    arr = window.snapshot(renderer, 'test_slicer.png', offscreen=True)
    import scipy
    print(scipy.__version__)
    print(scipy.__file__)

    print(arr.sum())
    print(np.sum(arr == 0))
    print(np.sum(arr > 0))
    print(arr.shape)
    print(arr.dtype)

    report = window.analyze_snapshot(arr, find_objects=True)

    npt.assert_equal(report.objects, 1)
    # print(arr[..., 0])

    # The slicer can cut directly a smaller part of the image
    slicer.display_extent(10, 30, 10, 30, 35, 35)
    renderer.ResetCamera()

    renderer.add(slicer)

    # save pixels in png file not a numpy array
    with InTemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, 'slice.png')
        # window.show(renderer)
        window.snapshot(renderer, fname, offscreen=True)
        report = window.analyze_snapshot(fname, find_objects=True)
        npt.assert_equal(report.objects, 1)

    npt.assert_raises(ValueError, actor.slicer, np.ones(10))

    renderer.clear()

    rgb = np.zeros((30, 30, 30, 3))
    rgb[..., 0] = 1.
    rgb_actor = actor.slicer(rgb)

    renderer.add(rgb_actor)

    renderer.reset_camera()
    renderer.reset_clipping_range()

    arr = window.snapshot(renderer, offscreen=True)
    report = window.analyze_snapshot(arr, colors=[(255, 0, 0)])
    npt.assert_equal(report.objects, 1)
    npt.assert_equal(report.colors_found, [True])

    lut = actor.colormap_lookup_table(scale_range=(0, 255),
                                      hue_range=(0.4, 1.),
                                      saturation_range=(1, 1.),
                                      value_range=(0., 1.))
    renderer.clear()
    slicer_lut = actor.slicer(data, lookup_colormap=lut)

    slicer_lut.display(10, None, None)
    slicer_lut.display(None, 10, None)
    slicer_lut.display(None, None, 10)

    slicer_lut.opacity(0.5)
    slicer_lut.tolerance(0.03)
    slicer_lut2 = slicer_lut.copy()
    npt.assert_equal(slicer_lut2.GetOpacity(), 0.5)
    npt.assert_equal(slicer_lut2.picker.GetTolerance(), 0.03)
    slicer_lut2.opacity(1)
    slicer_lut2.tolerance(0.025)
    slicer_lut2.display(None, None, 10)
    renderer.add(slicer_lut2)

    renderer.reset_clipping_range()

    arr = window.snapshot(renderer, offscreen=True)
    report = window.analyze_snapshot(arr, find_objects=True)
    npt.assert_equal(report.objects, 1)

    renderer.clear()

    data = (255 * np.random.rand(50, 50, 50))
    affine = np.diag([1, 3, 2, 1])
    slicer = actor.slicer(data, affine, interpolation='nearest')
    slicer.display(None, None, 25)

    renderer.add(slicer)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    arr = window.snapshot(renderer, offscreen=True)
    report = window.analyze_snapshot(arr, find_objects=True)
    npt.assert_equal(report.objects, 1)
    npt.assert_equal(data.shape, slicer.shape)

    renderer.clear()

    data = (255 * np.random.rand(50, 50, 50))
    affine = np.diag([1, 3, 2, 1])

    from dipy.align.reslice import reslice

    data2, affine2 = reslice(data, affine, zooms=(1, 3, 2),
                             new_zooms=(1, 1, 1))

    slicer = actor.slicer(data2, affine2, interpolation='linear')
    slicer.display(None, None, 25)

    renderer.add(slicer)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    # window.show(renderer, reset_camera=False)
    arr = window.snapshot(renderer, offscreen=True)
    report = window.analyze_snapshot(arr, find_objects=True)
    npt.assert_equal(report.objects, 1)
    npt.assert_array_equal([1, 3, 2] * np.array(data.shape),
                           np.array(slicer.shape))


@npt.dec.skipif(skip_it)
@xvfb_it
def test_surface():

    size = 11
    vertices = list()
    for i in range(-size, size):
        for j in range(-size, size):
            fact1 = - math.sin(i) * math.cos(j)
            fact2 = - math.exp(abs(1 - math.sqrt(i ** 2 + j ** 2) / math.pi))
            z_coord = -abs(fact1 * fact2)
            vertices.append([i, j, z_coord])

    c_arr = np.random.rand(len(vertices), 3)
    random.shuffle(vertices)
    vertices = np.array(vertices)
    tri = Delaunay(vertices[:, [0, 1]])
    faces = tri.simplices
    renderer_1 = window.renderer(background=(1, 1, 1))
    renderer_2 = window.renderer(background=(1, 1, 1))
    renderer_3 = window.renderer(background=(1, 1, 1))
    renderer_4 = window.renderer(background=(1, 1, 1))
    renderer_5 = window.renderer(background=(1, 1, 1))
    renderer_6 = window.renderer(background=(1, 1, 1))
    renderer_7 = window.renderer(background=(1, 1, 1))
    renderer_8 = window.renderer(background=(1, 1, 1))
    renderer_9 = window.renderer(background=(1, 1, 1))
    renderer_10 = window.renderer(background=(1, 1, 1))
    renderer_11 = window.renderer(background=(1, 1, 1))
    renderer_12 = window.renderer(background=(1, 1, 1))

    surface_actor_1 = actor.surface(vertices)
    surface_actor_2 = actor.surface(vertices, faces=faces)
    surface_actor_3 = actor.surface(vertices, colors=c_arr)
    surface_actor_4 = actor.surface(vertices, faces=faces, colors=c_arr)
    surface_actor_5 = actor.surface(vertices, smooth="butterfly")
    surface_actor_6 = actor.surface(vertices, faces=faces, smooth="butterfly")
    surface_actor_7 = actor.surface(vertices, colors=c_arr, smooth="butterfly")
    surface_actor_8 = actor.surface(vertices, faces=faces, colors=c_arr, smooth="butterfly")
    surface_actor_9 = actor.surface(vertices, smooth="loop")
    surface_actor_10 = actor.surface(vertices, faces=faces, smooth="loop")
    surface_actor_11 = actor.surface(vertices, colors=c_arr, smooth="loop")
    surface_actor_12 = actor.surface(vertices, faces=faces, colors=c_arr, smooth="loop")

    axes_actor = actor.axes(scale=(12, 12, 12))
    renderer_1.add(axes_actor)
    renderer_2.add(axes_actor)
    renderer_3.add(axes_actor)
    renderer_4.add(axes_actor)
    renderer_5.add(axes_actor)
    renderer_6.add(axes_actor)
    renderer_7.add(axes_actor)
    renderer_8.add(axes_actor)
    renderer_9.add(axes_actor)
    renderer_10.add(axes_actor)
    renderer_11.add(axes_actor)
    renderer_12.add(axes_actor)

    renderer_1.add(surface_actor_1)
    renderer_2.add(surface_actor_2)
    renderer_3.add(surface_actor_3)
    renderer_4.add(surface_actor_4)
    renderer_5.add(surface_actor_5)
    renderer_6.add(surface_actor_6)
    renderer_7.add(surface_actor_7)
    renderer_8.add(surface_actor_8)
    renderer_9.add(surface_actor_9)
    renderer_10.add(surface_actor_10)
    renderer_11.add(surface_actor_11)
    renderer_12.add(surface_actor_12)

    arr_1 = window.snapshot(renderer_1, 'test_surface_1.png', offscreen=True)
    arr_2 = window.snapshot(renderer_2, 'test_surface_2.png', offscreen=True)
    arr_3 = window.snapshot(renderer_3, 'test_surface_3.png', offscreen=True)
    arr_4 = window.snapshot(renderer_4, 'test_surface_4.png', offscreen=True)
    arr_5 = window.snapshot(renderer_5, 'test_surface_5.png', offscreen=True)
    arr_6 = window.snapshot(renderer_6, 'test_surface_6.png', offscreen=True)
    arr_7 = window.snapshot(renderer_7, 'test_surface_7.png', offscreen=True)
    arr_8 = window.snapshot(renderer_8, 'test_surface_8.png', offscreen=True)
    arr_9 = window.snapshot(renderer_9, 'test_surface_9.png', offscreen=True)
    arr_10 = window.snapshot(renderer_10, 'test_surface_10.png', offscreen=True)
    arr_11 = window.snapshot(renderer_11, 'test_surface_11.png', offscreen=True)
    arr_12 = window.snapshot(renderer_12, 'test_surface_12.png', offscreen=True)

    report_1 = window.analyze_snapshot(arr_1, find_objects=True)
    npt.assert_equal(report_1.objects, 1)

    report_2 = window.analyze_snapshot(arr_2, find_objects=True)
    npt.assert_equal(report_2.objects, 1)

    report_3 = window.analyze_snapshot(arr_3, find_objects=True)
    npt.assert_equal(report_3.objects, 1)

    report_4 = window.analyze_snapshot(arr_4, find_objects=True)
    npt.assert_equal(report_4.objects, 1)

    report_5 = window.analyze_snapshot(arr_5, find_objects=True)
    npt.assert_equal(report_5.objects, 1)

    report_6 = window.analyze_snapshot(arr_6, find_objects=True)
    npt.assert_equal(report_6.objects, 1)

    report_7 = window.analyze_snapshot(arr_7, find_objects=True)
    npt.assert_equal(report_7.objects, 1)

    report_8 = window.analyze_snapshot(arr_8, find_objects=True)
    npt.assert_equal(report_8.objects, 1)

    report_9 = window.analyze_snapshot(arr_9, find_objects=True)
    npt.assert_equal(report_9.objects, 1)

    report_10 = window.analyze_snapshot(arr_10, find_objects=True)
    npt.assert_equal(report_10.objects, 1)

    report_11 = window.analyze_snapshot(arr_11, find_objects=True)
    npt.assert_equal(report_11.objects, 1)

    report_12 = window.analyze_snapshot(arr_12, find_objects=True)
    npt.assert_equal(report_12.objects, 1)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_contour_from_roi():

    # Render volume
    renderer = window.renderer()
    data = np.zeros((50, 50, 50))
    data[20:30, 25, 25] = 1.
    data[25, 20:30, 25] = 1.
    affine = np.eye(4)
    surface = actor.contour_from_roi(data, affine,
                                     color=np.array([1, 0, 1]),
                                     opacity=.5)
    renderer.add(surface)

    renderer.reset_camera()
    renderer.reset_clipping_range()
    # window.show(renderer)

    # Test binarization
    renderer2 = window.renderer()
    data2 = np.zeros((50, 50, 50))
    data2[20:30, 25, 25] = 1.
    data2[35:40, 25, 25] = 1.
    affine = np.eye(4)
    surface2 = actor.contour_from_roi(data2, affine,
                                      color=np.array([0, 1, 1]),
                                      opacity=.5)
    renderer2.add(surface2)

    renderer2.reset_camera()
    renderer2.reset_clipping_range()
    # window.show(renderer2)

    arr = window.snapshot(renderer, 'test_surface.png', offscreen=True)
    arr2 = window.snapshot(renderer2, 'test_surface2.png', offscreen=True)

    report = window.analyze_snapshot(arr, find_objects=True)
    report2 = window.analyze_snapshot(arr2, find_objects=True)

    npt.assert_equal(report.objects, 1)
    npt.assert_equal(report2.objects, 2)

    # test on real streamlines using tracking example
    from dipy.data import read_stanford_labels
    from dipy.reconst.shm import CsaOdfModel
    from dipy.data import default_sphere
    from dipy.direction import peaks_from_model
    from dipy.tracking.local import ThresholdTissueClassifier
    from dipy.tracking import utils
    from dipy.tracking.local import LocalTracking
    from fury.colormap import line_colors

    hardi_img, gtab, labels_img = read_stanford_labels()
    data = hardi_img.get_data()
    labels = labels_img.get_data()
    affine = hardi_img.affine

    white_matter = (labels == 1) | (labels == 2)

    csa_model = CsaOdfModel(gtab, sh_order=6)
    csa_peaks = peaks_from_model(csa_model, data, default_sphere,
                                 relative_peak_threshold=.8,
                                 min_separation_angle=45,
                                 mask=white_matter)

    classifier = ThresholdTissueClassifier(csa_peaks.gfa, .25)

    seed_mask = labels == 2
    seeds = utils.seeds_from_mask(seed_mask, density=[1, 1, 1], affine=affine)

    # Initialization of LocalTracking.
    # The computation happens in the next step.
    streamlines = LocalTracking(csa_peaks, classifier, seeds, affine,
                                step_size=2)

    # Compute streamlines and store as a list.
    streamlines = list(streamlines)

    # Prepare the display objects.
    streamlines_actor = actor.line(streamlines, line_colors(streamlines))
    seedroi_actor = actor.contour_from_roi(seed_mask, affine, [0, 1, 1], 0.5)

    # Create the 3d display.
    r = window.Renderer()
    r2 = window.Renderer()
    r.add(streamlines_actor)
    arr3 = window.snapshot(r, 'test_surface3.png', offscreen=True)
    report3 = window.analyze_snapshot(arr3, find_objects=True)
    r2.add(streamlines_actor)
    r2.add(seedroi_actor)
    arr4 = window.snapshot(r2, 'test_surface4.png', offscreen=True)
    report4 = window.analyze_snapshot(arr4, find_objects=True)

    # assert that the seed ROI rendering is not far
    # away from the streamlines (affine error)
    npt.assert_equal(report3.objects, report4.objects)
    # window.show(r)
    # window.show(r2)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_streamtube_and_line_actors():
    renderer = window.renderer()

    line1 = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2.]])
    line2 = line1 + np.array([0.5, 0., 0.])

    lines = [line1, line2]
    colors = np.array([[1, 0, 0], [0, 0, 1.]])
    c = actor.line(lines, colors, linewidth=3)
    window.add(renderer, c)

    c = actor.line(lines, colors, spline_subdiv=5, linewidth=3)
    window.add(renderer, c)

    # create streamtubes of the same lines and shift them a bit
    c2 = actor.streamtube(lines, colors, linewidth=.1)
    c2.SetPosition(2, 0, 0)
    window.add(renderer, c2)

    arr = window.snapshot(renderer)

    report = window.analyze_snapshot(arr,
                                     colors=[(255, 0, 0), (0, 0, 255)],
                                     find_objects=True)

    npt.assert_equal(report.objects, 4)
    npt.assert_equal(report.colors_found, [True, True])

    # as before with splines
    c2 = actor.streamtube(lines, colors, spline_subdiv=5, linewidth=.1)
    c2.SetPosition(2, 0, 0)
    window.add(renderer, c2)

    arr = window.snapshot(renderer)

    report = window.analyze_snapshot(arr,
                                     colors=[(255, 0, 0), (0, 0, 255)],
                                     find_objects=True)

    npt.assert_equal(report.objects, 4)
    npt.assert_equal(report.colors_found, [True, True])


@npt.dec.skipif(skip_it or not have_dipy)
@xvfb_it
def test_bundle_maps():
    renderer = window.renderer()
    bundle = fornix_streamlines()
    bundle, shift = center_streamlines(bundle)

    mat = np.array([[1, 0, 0, 100],
                    [0, 1, 0, 100],
                    [0, 0, 1, 100],
                    [0, 0, 0, 1.]])

    bundle = transform_streamlines(bundle, mat)

    # metric = np.random.rand(*(200, 200, 200))
    metric = 100 * np.ones((200, 200, 200))

    # add lower values
    metric[100, :, :] = 100 * 0.5

    # create a nice orange-red colormap
    lut = actor.colormap_lookup_table(scale_range=(0., 100.),
                                      hue_range=(0., 0.1),
                                      saturation_range=(1, 1),
                                      value_range=(1., 1))

    line = actor.line(bundle, metric, linewidth=0.1, lookup_colormap=lut)
    window.add(renderer, line)
    window.add(renderer, actor.scalar_bar(lut, ' '))

    report = window.analyze_renderer(renderer)

    npt.assert_almost_equal(report.actors, 1)
    # window.show(renderer)

    renderer.clear()

    nb_points = np.sum([len(b) for b in bundle])
    values = 100 * np.random.rand(nb_points)
    # values[:nb_points/2] = 0

    line = actor.streamtube(bundle, values, linewidth=0.1, lookup_colormap=lut)
    renderer.add(line)
    # window.show(renderer)

    report = window.analyze_renderer(renderer)
    npt.assert_equal(report.actors_classnames[0], 'vtkLODActor')

    renderer.clear()

    colors = np.random.rand(nb_points, 3)
    # values[:nb_points/2] = 0

    line = actor.line(bundle, colors, linewidth=2)
    renderer.add(line)
    # window.show(renderer)

    report = window.analyze_renderer(renderer)
    npt.assert_equal(report.actors_classnames[0], 'vtkLODActor')
    # window.show(renderer)

    arr = window.snapshot(renderer)
    report2 = window.analyze_snapshot(arr)
    npt.assert_equal(report2.objects, 1)

    # try other input options for colors
    renderer.clear()
    actor.line(bundle, (1., 0.5, 0))
    actor.line(bundle, np.arange(len(bundle)))
    actor.line(bundle)
    colors = [np.random.rand(*b.shape) for b in bundle]
    actor.line(bundle, colors=colors)


@npt.dec.skipif(skip_it or not have_dipy)
@xvfb_it
def test_odf_slicer(interactive=False):

    sphere = get_sphere('symmetric362')

    shape = (11, 11, 11, sphere.vertices.shape[0])

    fid, fname = mkstemp(suffix='_odf_slicer.mmap')
    print(fid)
    print(fname)

    odfs = np.memmap(fname, dtype=np.float64, mode='w+',
                     shape=shape)

    odfs[:] = 1

    affine = np.eye(4)
    renderer = window.Renderer()

    mask = np.ones(odfs.shape[:3])
    mask[:4, :4, :4] = 0

    odfs[..., 0] = 1

    odf_actor = actor.odf_slicer(odfs, affine,
                                 mask=mask, sphere=sphere, scale=.25,
                                 colormap='plasma')
    fa = 0. * np.zeros(odfs.shape[:3])
    fa[:, 0, :] = 1.
    fa[:, -1, :] = 1.
    fa[0, :, :] = 1.
    fa[-1, :, :] = 1.
    fa[5, 5, 5] = 1

    k = 5
    I, J, K = odfs.shape[:3]

    fa_actor = actor.slicer(fa, affine)
    fa_actor.display_extent(0, I, 0, J, k, k)
    renderer.add(odf_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    odf_actor.display_extent(0, I, 0, J, k, k)
    odf_actor.GetProperty().SetOpacity(1.0)
    if interactive:
        window.show(renderer, reset_camera=False)

    arr = window.snapshot(renderer)
    report = window.analyze_snapshot(arr, find_objects=True)
    npt.assert_equal(report.objects, 11 * 11)

    renderer.clear()
    renderer.add(fa_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()
    if interactive:
        window.show(renderer)

    mask[:] = 0
    mask[5, 5, 5] = 1
    fa[5, 5, 5] = 0
    fa_actor = actor.slicer(fa, None)
    fa_actor.display(None, None, 5)
    odf_actor = actor.odf_slicer(odfs, None, mask=mask,
                                 sphere=sphere, scale=.25,
                                 colormap='plasma',
                                 norm=False, global_cm=True)
    renderer.clear()
    renderer.add(fa_actor)
    renderer.add(odf_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()
    if interactive:
        window.show(renderer)

    renderer.clear()
    renderer.add(odf_actor)
    renderer.add(fa_actor)
    odfs[:, :, :] = 1
    mask = np.ones(odfs.shape[:3])
    odf_actor = actor.odf_slicer(odfs, None, mask=mask,
                                 sphere=sphere, scale=.25,
                                 colormap='plasma',
                                 norm=False, global_cm=True)

    renderer.clear()
    renderer.add(odf_actor)
    renderer.add(fa_actor)
    renderer.add(actor.axes((11, 11, 11)))
    for i in range(11):
        odf_actor.display(i, None, None)
        fa_actor.display(i, None, None)
        if interactive:
            window.show(renderer)
    for j in range(11):
        odf_actor.display(None, j, None)
        fa_actor.display(None, j, None)
        if interactive:
            window.show(renderer)
    # with mask equal to zero everything should be black
    mask = np.zeros(odfs.shape[:3])
    odf_actor = actor.odf_slicer(odfs, None, mask=mask,
                                 sphere=sphere, scale=.25,
                                 colormap='plasma',
                                 norm=False, global_cm=True)
    renderer.clear()
    renderer.add(odf_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()
    if interactive:
        window.show(renderer)

    report = window.analyze_renderer(renderer)
    npt.assert_equal(report.actors, 1)
    npt.assert_equal(report.actors_classnames[0], 'vtkLODActor')

    del odf_actor
    odfs._mmap.close()
    del odfs
    os.close(fid)

    os.remove(fname)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_peak_slicer(interactive=False):

    _peak_dirs = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype='f4')
    # peak_dirs.shape = (1, 1, 1) + peak_dirs.shape

    peak_dirs = np.zeros((11, 11, 11, 3, 3))

    peak_values = np.random.rand(11, 11, 11, 3)

    peak_dirs[:, :, :] = _peak_dirs

    renderer = window.Renderer()
    peak_actor = actor.peak_slicer(peak_dirs)
    renderer.add(peak_actor)
    renderer.add(actor.axes((11, 11, 11)))
    if interactive:
        window.show(renderer)

    renderer.clear()
    renderer.add(peak_actor)
    renderer.add(actor.axes((11, 11, 11)))
    for k in range(11):
        peak_actor.display_extent(0, 10, 0, 10, k, k)

    for j in range(11):
        peak_actor.display_extent(0, 10, j, j, 0, 10)

    for i in range(11):
        peak_actor.display(i, None, None)

    renderer.rm_all()

    peak_actor = actor.peak_slicer(
        peak_dirs,
        peak_values,
        mask=None,
        affine=np.diag([3, 2, 1, 1]),
        colors=None,
        opacity=1,
        linewidth=3,
        lod=True,
        lod_points=10 ** 4,
        lod_points_size=3)

    renderer.add(peak_actor)
    renderer.add(actor.axes((11, 11, 11)))
    if interactive:
        window.show(renderer)

    report = window.analyze_renderer(renderer)
    ex = ['vtkLODActor', 'vtkOpenGLActor', 'vtkOpenGLActor', 'vtkOpenGLActor']
    npt.assert_equal(report.actors_classnames, ex)


@npt.dec.skipif(skip_it or not have_dipy)
@xvfb_it
def test_tensor_slicer(interactive=False):

    evals = np.array([1.4, .35, .35]) * 10 ** (-3)
    evecs = np.eye(3)

    mevals = np.zeros((3, 2, 4, 3))
    mevecs = np.zeros((3, 2, 4, 3, 3))

    mevals[..., :] = evals
    mevecs[..., :, :] = evecs

    from dipy.data import get_sphere

    sphere = get_sphere('symmetric724')

    affine = np.eye(4)
    renderer = window.Renderer()

    tensor_actor = actor.tensor_slicer(mevals, mevecs, affine=affine,
                                       sphere=sphere,  scale=.3)
    I, J, K = mevals.shape[:3]
    renderer.add(tensor_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    tensor_actor.display_extent(0, 1, 0, J, 0, K)
    tensor_actor.GetProperty().SetOpacity(1.0)
    if interactive:
        window.show(renderer, reset_camera=False)

    npt.assert_equal(renderer.GetActors().GetNumberOfItems(), 1)

    # Test extent
    big_extent = renderer.GetActors().GetLastActor().GetBounds()
    big_extent_x = abs(big_extent[1] - big_extent[0])
    tensor_actor.display(x=2)

    if interactive:
        window.show(renderer, reset_camera=False)

    small_extent = renderer.GetActors().GetLastActor().GetBounds()
    small_extent_x = abs(small_extent[1] - small_extent[0])
    npt.assert_equal(big_extent_x > small_extent_x, True)

    # Test empty mask
    empty_actor = actor.tensor_slicer(mevals, mevecs, affine=affine,
                                      mask=np.zeros(mevals.shape[:3]),
                                      sphere=sphere,  scale=.3)
    npt.assert_equal(empty_actor.GetMapper(), None)

    # Test mask
    mask = np.ones(mevals.shape[:3])
    mask[:2, :3, :3] = 0
    cfa = color_fa(fractional_anisotropy(mevals), mevecs)
    tensor_actor = actor.tensor_slicer(mevals, mevecs, affine=affine,
                                       mask=mask, scalar_colors=cfa,
                                       sphere=sphere,  scale=.3)
    renderer.clear()
    renderer.add(tensor_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    if interactive:
        window.show(renderer, reset_camera=False)

    mask_extent = renderer.GetActors().GetLastActor().GetBounds()
    mask_extent_x = abs(mask_extent[1] - mask_extent[0])
    npt.assert_equal(big_extent_x > mask_extent_x, True)

    # test display
    tensor_actor.display()
    current_extent = renderer.GetActors().GetLastActor().GetBounds()
    current_extent_x = abs(current_extent[1] - current_extent[0])
    npt.assert_equal(big_extent_x > current_extent_x, True)
    if interactive:
        window.show(renderer, reset_camera=False)

    tensor_actor.display(y=1)
    current_extent = renderer.GetActors().GetLastActor().GetBounds()
    current_extent_y = abs(current_extent[3] - current_extent[2])
    big_extent_y = abs(big_extent[3] - big_extent[2])
    npt.assert_equal(big_extent_y > current_extent_y, True)
    if interactive:
        window.show(renderer, reset_camera=False)

    tensor_actor.display(z=1)
    current_extent = renderer.GetActors().GetLastActor().GetBounds()
    current_extent_z = abs(current_extent[5] - current_extent[4])
    big_extent_z = abs(big_extent[5] - big_extent[4])
    npt.assert_equal(big_extent_z > current_extent_z, True)
    if interactive:
        window.show(renderer, reset_camera=False)

    # Test error handling of the method when
    # incompatible dimension of mevals and evecs are passed.
    mevals = np.zeros((3, 2, 3))
    mevecs = np.zeros((3, 2, 4, 3, 3))

    with npt.assert_raises(RuntimeError):
        tensor_actor = actor.tensor_slicer(mevals, mevecs, affine=affine,
                                           mask=mask, scalar_colors=cfa,
                                           sphere=sphere, scale=.3)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_dots(interactive=False):
    points = np.array([[0, 0, 0], [0, 1, 0], [1, 0, 0]])

    dots_actor = actor.dots(points, color=(0, 255, 0))

    renderer = window.Renderer()
    renderer.add(dots_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    if interactive:
        window.show(renderer, reset_camera=False)

    npt.assert_equal(renderer.GetActors().GetNumberOfItems(), 1)

    extent = renderer.GetActors().GetLastActor().GetBounds()
    npt.assert_equal(extent, (0.0, 1.0, 0.0, 1.0, 0.0, 0.0))

    arr = window.snapshot(renderer)
    report = window.analyze_snapshot(arr,
                                     colors=(0, 255, 0))
    npt.assert_equal(report.objects, 3)

    # Test one point
    points = np.array([0, 0, 0])
    dot_actor = actor.dots(points, color=(0, 0, 255))

    renderer.clear()
    renderer.add(dot_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    arr = window.snapshot(renderer)
    report = window.analyze_snapshot(arr,
                                     colors=(0, 0, 255))
    npt.assert_equal(report.objects, 1)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_points(interactive=False):
    points = np.array([[0, 0, 0], [0, 1, 0], [1, 0, 0]])
    colors = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    points_actor = actor.point(points,  colors)

    renderer = window.Renderer()
    renderer.add(points_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    if interactive:
        window.show(renderer, reset_camera=False)

    npt.assert_equal(renderer.GetActors().GetNumberOfItems(), 1)

    arr = window.snapshot(renderer)
    report = window.analyze_snapshot(arr,
                                     colors=colors)
    npt.assert_equal(report.objects, 3)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_labels(interactive=False):

    text_actor = actor.label("Hello")

    renderer = window.Renderer()
    renderer.add(text_actor)
    renderer.reset_camera()
    renderer.reset_clipping_range()

    if interactive:
        window.show(renderer, reset_camera=False)

    npt.assert_equal(renderer.GetActors().GetNumberOfItems(), 1)


@npt.dec.skipif(skip_it)
@xvfb_it
def test_spheres(interactive=False):

    xyzr = np.array([[0, 0, 0, 10], [100, 0, 0, 25], [200, 0, 0, 50]])
    colors = np.array([[1, 0, 0, 0.3], [0, 1, 0, 0.4], [0, 0, 1., 0.99]])

    renderer = window.Renderer()
    sphere_actor = actor.sphere(centers=xyzr[:, :3], colors=colors[:],
                                radii=xyzr[:, 3])
    renderer.add(sphere_actor)

    if interactive:
        window.show(renderer, order_transparent=True)

    arr = window.snapshot(renderer)
    report = window.analyze_snapshot(arr,
                                     colors=colors)
    npt.assert_equal(report.objects, 3)


if __name__ == "__main__":
    npt.run_module_suite()
