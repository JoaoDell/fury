import os
from typing import Any
from functools import partial

import numpy as np
from fury.actor import Actor, billboard
from fury.colormap import create_colormap
from fury.io import load_image
from fury.lib import Texture, WindowToImageFilter
from fury.shaders import (attribute_to_actor,
                          compose_shader,
                          import_fury_shader,
                          shader_apply_effects,
                          shader_custom_uniforms)
from fury.utils import rgb_to_vtk
from fury.window import (gl_disable_depth,
                         gl_set_additive_blending,
                         RenderWindow,
                         Scene,
                         ShowManager)


WRAP_MODE_DIC = {"clamptoedge" : Texture.ClampToEdge,
                 "repeat" : Texture.Repeat,
                 "mirroredrepeat" : Texture.MirroredRepeat,
                 "clamptoborder" : Texture.ClampToBorder}

BLENDING_MODE_DIC = {"none" : 0, "replace" : 1,
                     "modulate" : 2, "add" : 3,
                     "addsigned" : 4, "interpolate" : 5,
                     "subtract" : 6}


def window_to_texture(
        window : RenderWindow,
        texture_name : str,
        target_actor : Actor,
        blending_mode : str = "None",
        wrap_mode : str = "ClampToBorder",
        border_color : tuple = (
            0.0,
            0.0,
            0.0,
            1.0),
        interpolate : bool = True,
        d_type : str = "rgb"):
    """Capture a rendered window and pass it as a texture to the given actor.

    Parameters
    ----------
    window : window.RenderWindow
        Window to be captured.
    texture_name : str
        Name of the texture to be passed to the actor.
    target_actor : Actor
        Target actor to receive the texture.
    blending_mode : str, optional
        Texture blending mode. The options are:
        1. None
        2. Replace
        3. Modulate
        4. Add
        5. AddSigned
        6. Interpolate
        7. Subtract
    wrap_mode : str, optional
        Texture wrapping mode. The options are:
        1. ClampToEdge
        2. Repeat
        3. MirroredRepeat
        4. ClampToBorder
    border_color : tuple (4, ), optional
        Texture RGBA border color.
    interpolate : bool, optional
        Texture interpolation.
    d_type : str, optional
        Texture pixel type, "rgb" or "rgba". Default is "rgb"
    """

    windowToImageFilter = WindowToImageFilter()
    windowToImageFilter.SetInput(window)
    type_dic = {"rgb" : windowToImageFilter.SetInputBufferTypeToRGB,
                "rgba" : windowToImageFilter.SetInputBufferTypeToRGBA,
                "zbuffer" : windowToImageFilter.SetInputBufferTypeToZBuffer}
    type_dic[d_type.lower()]()

    texture = Texture()
    texture.SetMipmap(True)
    texture.SetInputConnection(windowToImageFilter.GetOutputPort())
    texture.SetBorderColor(*border_color)
    texture.SetWrap(WRAP_MODE_DIC[wrap_mode.lower()])
    texture.SetInterpolate(interpolate)
    texture.SetBlendingMode(BLENDING_MODE_DIC[blending_mode.lower()])

    target_actor.GetProperty().SetTexture(texture_name, texture)


def texture_to_actor(
        path_to_texture : str,
        texture_name : str,
        target_actor : Actor,
        blending_mode : str = "None",
        wrap_mode : str = "ClampToBorder",
        border_color : tuple = (
            0.0,
            0.0,
            0.0,
            1.0),
        interpolate : bool = True):
    """Pass an imported texture to an actor.

    Parameters
    ----------
    path_to_texture : str
        Texture image path.
    texture_name : str
        Name of the texture to be passed to the actor.
    target_actor : Actor
        Target actor to receive the texture.
    blending_mode : str, optional
        Texture blending mode. The options are:
        1. None
        2. Replace
        3. Modulate
        4. Add
        5. AddSigned
        6. Interpolate
        7. Subtract
    wrap_mode : str, optional
        Texture wrapping mode. The options are:
        1. ClampToEdge
        2. Repeat
        3. MirroredRepeat
        4. ClampToBorder
    border_color : tuple (4, ), optional
        Texture RGBA border color.
    interpolate : bool, optional
        Texture interpolation."""

    texture = Texture()

    textureArray = load_image(path_to_texture)
    textureData = rgb_to_vtk(textureArray)

    texture.SetInputDataObject(textureData)
    texture.SetBorderColor(*border_color)
    texture.SetWrap(WRAP_MODE_DIC[wrap_mode.lower()])
    texture.SetInterpolate(interpolate)
    texture.MipmapOn()
    texture.SetBlendingMode(BLENDING_MODE_DIC[blending_mode.lower()])

    target_actor.GetProperty().SetTexture(texture_name, texture)

def colormap_to_texture(
        colormap : np.array,
        texture_name : str,
        target_actor : Actor,
        interpolate : bool = True):
    """Convert a colormap to a texture and pass it to an actor.

    Parameters
    ----------
    colormap : np.array (N, 4) or (1, N, 4)
        RGBA color map array. The array can be two dimensional, although a three dimensional one is preferred.
    texture_name : str
        Name of the color map texture to be passed to the actor.
    target_actor : Actor
        Target actor to receive the color map texture.
    interpolate : bool, optional
        Color map texture interpolation."""

    if len(colormap.shape) == 2:
        colormap = np.array([colormap])

    texture = Texture()

    cmap = (255*colormap).astype(np.uint8)
    cmap = rgb_to_vtk(cmap)

    texture.SetInputDataObject(cmap)
    texture.SetWrap(Texture.ClampToEdge)
    texture.SetInterpolate(interpolate)
    texture.MipmapOn()
    texture.SetBlendingMode(0)

    target_actor.GetProperty().SetTexture(texture_name, texture)



class EffectManager():
    """Class that manages the application of post-processing effects on actors.

    Parameters
    ----------
    manager : ShowManager
        Target manager that will render post processed actors."""

    def __init__(self, manager : ShowManager):
        self.scene = Scene()
        cam_params = manager.scene.get_camera()
        self.scene.set_camera(*cam_params)
        self.on_manager = manager
        self.off_manager = ShowManager(self.scene,
                                       size=manager.size)
        self.off_manager.window.SetOffScreenRendering(True)
        self.off_manager.initialize()
        self._n_active_effects = 0
        self._active_effects = {}

    def add(self, effect):
        callback = partial(effect, effect_manager=self)
        if hasattr(effect, "apply"):
            effect.apply(self)

        callback()
        callback_id = self.on_manager.add_iren_callback(callback, "RenderEvent")


        self._active_effects[effect.textured_billboard] = (callback_id, effect.bill)
        self._n_active_effects += 1
        self.on_manager.scene.add(effect.textured_billboard)

        return effect.textured_billboard

    def remove_effect(self, effect_actor):
        """Remove an existing effect from the effects manager.
        Beware that the effect and the actor will be removed from the rendering pipeline
        and shall not work after this action.

        Parameters
        ----------
        effect_actor : actor.Actor
            Actor of effect to be removed.
        """
        if self._n_active_effects > 0:
            self.on_manager.iren.RemoveObserver(self._active_effects[effect_actor][0])
            self.off_manager.scene.RemoveActor(self._active_effects[effect_actor][1])
            self.on_manager.scene.RemoveActor(effect_actor)
            self._active_effects.pop(effect_actor)
            self._n_active_effects -= 1
        else:
            raise IndexError("Manager has no active effects.")

class KDE():
    def __init__(self,
            points : np.ndarray,
            bandwidths,
            kernel : str = "gaussian",
            opacity : float = 1.0,
            colormap : str = "viridis",
            custom_colormap : np.array = None):
        self.points = points
        self.bandwidths = bandwidths
        self.kernel = kernel
        self.opacity = opacity
        self.colormap = colormap
        self.custom_colormap = custom_colormap
        if not isinstance(bandwidths, np.ndarray):
            bandwidths = np.array([bandwidths])
        if bandwidths.shape[0] != 1 and bandwidths.shape[0] != points.shape[0]:
            raise IndexError("bandwidths size must be one or points size.")
        elif bandwidths.shape[0] == 1:
            bandwidths = np.repeat(bandwidths[0], points.shape[0])
        if np.min(bandwidths) <= 0:
            raise ValueError("bandwidths can't have zero or negative values.")

        kde_vs_dec = """
        in float in_bandwidth;
        varying float out_bandwidth;

        in float in_scale;
        varying float out_scale;
        """

        kde_vs_impl = """
        out_bandwidth = in_bandwidth;
        out_scale = in_scale;
        """


        varying_fs_dec = """
        varying float out_bandwidth;
        varying float out_scale;
        """

        kde_fs_dec = import_fury_shader(
            os.path.join("utils", f"{kernel.lower()}_distribution.glsl"))

        kde_fs_impl = """
        float current_kde = kde(normalizedVertexMCVSOutput*out_scale, out_bandwidth);
        color = vec3(current_kde);
        fragOutput0 = vec4(color, 1.0);
        """


        fs_dec = compose_shader([varying_fs_dec, kde_fs_dec])

        """Scales parameter will be defined by the empirical rule:
        1*bandwidth radius = 68.27% of data inside the curve
        2*bandwidth radius = 95.45% of data inside the curve
        3*bandwidth radius = 99.73% of data inside the curve"""
        scales = 2*3.0*np.copy(bandwidths)

        self.center_of_mass = np.average(points, axis=0)
        self.bill = billboard(
            points,
            (0.0,
             0.0,
             1.0),
            scales=scales,
            fs_dec=fs_dec,
            fs_impl=kde_fs_impl,
            vs_dec=kde_vs_dec,
            vs_impl=kde_vs_impl)
        self.scales = scales
        # Blending and uniforms setup

    def apply(self, effect_manager : EffectManager):
        self.effect_manager = effect_manager
        bandwidths = self.bandwidths
        opacity = self.opacity
        colormap = self.colormap
        custom_colormap = self.custom_colormap
        bill = self.bill
        scales = self.scales
        center_of_mass = self.center_of_mass

        off_window = effect_manager.off_manager.window
        shader_apply_effects(off_window, bill, gl_disable_depth)
        shader_apply_effects(off_window, bill, gl_set_additive_blending)
        attribute_to_actor(bill, np.repeat(bandwidths, 4), "in_bandwidth")
        attribute_to_actor(bill, np.repeat(scales, 4), "in_scale")

        if effect_manager._n_active_effects > 0:
            effect_manager.off_manager.scene.GetActors().GetLastActor().SetVisibility(False)
        effect_manager.off_manager.scene.add(self.bill)

        bill_bounds = self.bill.GetBounds()
        max_bandwidth = 2*4.0*np.max(bandwidths)

        actor_scales = np.array([[bill_bounds[1] - bill_bounds[0] +
                                  center_of_mass[0] + max_bandwidth,
                                  bill_bounds[3] - bill_bounds[2] +
                                  center_of_mass[1] + max_bandwidth, 0.0]])

        scale = np.array([[actor_scales.max(),
                           actor_scales.max(),
                           0.0]])

        self.res = np.array(effect_manager.off_manager.size)

        # Render to second billboard for color map post-processing.
        tex_dec = import_fury_shader(os.path.join("effects", "color_mapping.glsl"))

        tex_impl = """
        // Turning screen coordinates to texture coordinates
        vec2 tex_coords = gl_FragCoord.xy/res;
        float intensity = texture(screenTexture, tex_coords).r;

        if(intensity<=0.0){
            discard;
        }else{
            vec4 final_color = color_mapping(intensity, colormapTexture);
            fragOutput0 = vec4(final_color.rgb, u_opacity*final_color.a);
        }
        """
        textured_billboard = billboard(
            np.array([center_of_mass]),
            scales=scale,
            fs_dec=tex_dec,
            fs_impl=tex_impl)
        self.textured_billboard = textured_billboard
        shader_custom_uniforms(textured_billboard, "fragment").SetUniform2f("res", self.res)
        shader_custom_uniforms(textured_billboard, "fragment").SetUniformf("u_opacity", opacity)

        # Disables the texture warnings
        textured_billboard.GetProperty().GlobalWarningDisplayOff()

        if custom_colormap is None:
            cmap = create_colormap(np.arange(0.0, 1.0, 1/256), colormap)
        else:
            cmap = custom_colormap

        colormap_to_texture(cmap, "colormapTexture", textured_billboard)

    def __call__(self,  obj=None, event=None, effect_manager=None) -> Any:

        off_manager = effect_manager.off_manager
        on_manager = effect_manager.on_manager

        on_window = on_manager.window
        off_window = off_manager.window

        cam_params = effect_manager.on_manager.scene.get_camera()
        off_manager.scene.set_camera(*cam_params)
        self.res[0], self.res[1] = on_window.GetSize()
        off_window.SetSize(self.res[0], self.res[1])
        shader_custom_uniforms(self.textured_billboard, "fragment").SetUniform2f("res", self.res)
        off_manager.scene.Modified()
        shader_apply_effects(off_window, self.bill, gl_disable_depth)
        shader_apply_effects(off_window, self.bill, gl_set_additive_blending)
        off_manager.render()

        window_to_texture(
            off_manager.window,
            "screenTexture",
            self.textured_billboard,
            blending_mode="Interpolate",
            d_type="rgba")
