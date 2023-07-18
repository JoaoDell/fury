import numpy as np
from fury import window, actor
from fury.shaders import compose_shader, shader_apply_effects, attribute_to_actor
from fury.lib import Texture, WindowToImageFilter
from fury.io import load_image
from fury.utils import rgb_to_vtk
from matplotlib import colormaps


def window_to_texture(
        window : window.RenderWindow,
        texture_name : str,
        target_actor : actor.Actor,
        blending_mode : str = "None",
        wrap_mode : str = "ClampToBorder",
        border_color : tuple = (
            0.0,
            0.0,
            0.0,
            1.0),
        interpolate : bool = True):
    """Captures a rendered window and pass it as a texture to the given actor.

    Parameters
    ----------
    window : window.RenderWindow
        Window to be captured.
    texture_name : str
        Name of the texture to be passed to the actor.
    target_actor : actor.Actor
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

    wrap_mode_dic = {"ClampToEdge" : Texture.ClampToEdge,
                     "Repeat" : Texture.Repeat,
                     "MirroredRepeat" : Texture.MirroredRepeat,
                     "ClampToBorder" : Texture.ClampToBorder}

    blending_mode_dic = {"None" : 0, "Replace" : 1,
                         "Modulate" : 2, "Add" : 3,
                         "AddSigned" : 4, "Interpolate" : 5,
                         "Subtract" : 6}

    r, g, b, a = border_color

    windowToImageFilter = WindowToImageFilter()
    windowToImageFilter.SetInput(window)

    windowToImageFilter.Update()

    texture = Texture()
    texture.SetInputConnection(windowToImageFilter.GetOutputPort())
    texture.SetBorderColor(r, g, b, a)
    texture.SetWrap(wrap_mode_dic[wrap_mode])
    texture.SetInterpolate(interpolate)
    texture.MipmapOn()
    texture.SetBlendingMode(blending_mode_dic[blending_mode])

    target_actor.GetProperty().SetTexture(texture_name, texture)


def texture_to_actor(
        path_to_texture : str,
        texture_name : str,
        target_actor : actor.Actor,
        blending_mode : str = "None",
        wrap_mode : str = "ClampToBorder",
        border_color : tuple = (
            0.0,
            0.0,
            0.0,
            1.0),
        interpolate : bool = True):
    """Passes an imported texture to an actor.

    Parameters
    ----------
    path_to_texture : str
        Texture image path.
    texture_name : str
        Name of the texture to be passed to the actor.
    target_actor : actor.Actor
        Target actor to receive the texture.
    blending_mode : str
        Texture blending mode. The options are:
    1. None
    2. Replace
    3. Modulate
    4. Add
    5. AddSigned
    6. Interpolate
    7. Subtract

    wrap_mode : str
        Texture wrapping mode. The options are:
    1. ClampToEdge
    2. Repeat
    3. MirroredRepeat
    4. ClampToBorder

    border_color : tuple (4, )
        Texture RGBA border color.
    interpolate : bool
        Texture interpolation."""

    wrap_mode_dic = {"ClampToEdge" : Texture.ClampToEdge,
                     "Repeat" : Texture.Repeat,
                     "MirroredRepeat" : Texture.MirroredRepeat,
                     "ClampToBorder" : Texture.ClampToBorder}

    blending_mode_dic = {"None" : 0, "Replace" : 1,
                         "Modulate" : 2, "Add" : 3,
                         "AddSigned" : 4, "Interpolate" : 5,
                         "Subtract" : 6}

    r, g, b, a = border_color

    texture = Texture()

    colormapArray = load_image(path_to_texture)
    colormapData = rgb_to_vtk(colormapArray)

    texture.SetInputDataObject(colormapData)
    texture.SetBorderColor(r, g, b, a)
    texture.SetWrap(wrap_mode_dic[wrap_mode])
    texture.SetInterpolate(interpolate)
    texture.MipmapOn()
    texture.SetBlendingMode(blending_mode_dic[blending_mode])

    target_actor.GetProperty().SetTexture(texture_name, texture)


def colormap_to_texture(
        colormap : np.array,
        texture_name : str,
        target_actor : actor.Actor,
        interpolate : bool = True):
    """Converts a colormap to a texture and pass it to an actor.

    Parameters
    ----------
    colormap : np.array (N, 4) or (1, N, 4)
        RGBA color map array. The array can be two dimensional, although a three dimensional one is preferred.
    texture_name : str
        Name of the color map texture to be passed to the actor.
    target_actor : actor.Actor
        Target actor to receive the color map texture.
    interpolate : bool
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


def shader_custom_uniforms(actor : actor.Actor, shader_type : str):
    """Eases the passing of uniform values to the shaders by returning ``actor.GetShaderProperty().GetVertexCustomUniforms()``,
    that give access to the ``SetUniform`` methods.
    Parameters
    ----------
    actor : actor.Actor
          Actor which the uniform values will be passed to.
    shader_type : str
          Shader type of the uniform values to be passed. It can be:
          * "vertex"
          * "fragment"
          * "geometry"
    """
    if shader_type == "vertex":
        return actor.GetShaderProperty().GetVertexCustomUniforms()
    elif shader_type == "fragment":
        return actor.GetShaderProperty().GetFragmentCustomUniforms()
    elif shader_type == "geometry":
        return actor.GetShaderProperty().GetGeometryCustomUniforms()
    else:
        raise ValueError("Shader type unknown.")


def normalize(array : np.array, min : float = 0.0, max : float = 1.0, axis : int = 0):
    """Converts an array to a given desired range.

    Parameters
    ----------
    array : np.ndarray
    Array to be normalized.
    min : float
    Bottom value of the interval of normalization. If no value is given, it is passed as 0.0.
    max : float
    Upper value of the interval of normalization. If no value is given, it is passed as 1.0.

    Returns
    -------

    array : np.array
    Array converted to the given desired range.
    """
    if np.max(array) != np.min(array):
        return ((array - np.min(array))/(np.max(array) - np.min(array)))*(max - min) + min
    else:
        raise ValueError(
            "Can't normalize an array which maximum and minimum value are the same.")


kde_vs_dec = """
in float in_sigma;
varying float out_sigma;

in float in_scale;
varying float out_scale;
"""


kde_vs_impl = """
out_sigma = in_sigma;
out_scale = in_scale;
"""


kde_dec = """
varying float out_sigma;
varying float out_scale;
float kde(vec3 point, float sigma, float scale){
    return exp(-1.0*pow(length(point/scale), 2.0)/(2.0*sigma*sigma) );
}

vec3 color_mapping(float intensity, float normalizingFactor){
    float normalizedIntensity = intensity/normalizingFactor;
    return texture(colormapTexture, vec2(normalizedIntensity,0)).rgb;
}
"""

kde_impl = """
float current_kde = kde(normalizedVertexMCVSOutput, out_sigma, out_scale);

if(current_kde <= discard_value){
    discard;
}else{
    color = color_mapping(current_kde, 1.0).rgb;;
    fragOutput0 = vec4(color, 1.0);
}
"""



fs_dec = compose_shader([kde_dec])

fs_impl = compose_shader([kde_impl])


# Windows and scenes setup
width, height = (1920, 1080)
offWidth, offHeight = (1080, 1080)

offScene = window.Scene()

off_manager = window.ShowManager(
    offScene,
    "demo",
    (width,
     height),
    reset_camera=True,
    order_transparent=True)


off_manager.initialize()



n_points = 500
points = np.random.rand(n_points, 3)
points = normalize(points, -5, 5)
scales = np.random.rand(n_points, 1)
sigmas = normalize(np.random.rand(n_points, 1), 0.3, 0.5)

sigma = 0.25
scale = 0.5

billboard = actor.billboard(
    points,
    (0.0,
     0.0,
     1.0),
    scales=scales,
    fs_dec=fs_dec,
    fs_impl=fs_impl, 
    vs_dec=kde_vs_dec, 
    vs_impl=kde_vs_impl)

# Blending and uniforms setup
shader_apply_effects(off_manager.window, billboard, window.gl_disable_depth)
shader_apply_effects(off_manager.window, billboard, window.gl_set_additive_blending)
shader_custom_uniforms(billboard, "fragment").SetUniformf("sigma", sigma)
shader_custom_uniforms(billboard, "fragment").SetUniformf("discard_value", 0.0001)
attribute_to_actor(billboard, np.repeat(scales, 4), "in_scale")
attribute_to_actor(billboard, np.repeat(sigmas, 4), "in_sigma")

off_manager.scene.add(billboard)



# Render to second billboard for color map post-processing.
cmap = colormaps["inferno"]
cmap = np.array([cmap(i) for i in np.arange(0.0, 1.0, 1/256)])


colormap_to_texture(cmap, "colormapTexture", billboard)

off_manager.start()
