from kgen import ComfyUIClient4Flux, Scene

client = ComfyUIClient4Flux()

# create a sceneList with a single scene
# class Scene(TypedDict):
#     """A scene in the story/video."""
#
#     location: Annotated[str, "the location of the scene"]
#     time: Annotated[str, "the time of the scene"]
#     characters: Annotated[list[Character], "the characters in the scene"]
#     action: Annotated[str, "the action of the scene"]
#     image_prompt_positive: Annotated[
#         str, "the positive image prompt of the scene, used for image generation"
#     ]
#     image_prompt_negative: Annotated[
#         str, "the negative image prompt of the scene, used for image generation"
#     ]
#
#
# class SceneList(TypedDict):
#     """Collection of scenes."""
#
#     scenes: list[Scene]
#

scene = Scene(image_prompt_positive="a man under the tree")
sceneList =[scene]



client.generate_scene_images(sceneList)
