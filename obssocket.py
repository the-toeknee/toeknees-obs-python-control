from obswebsocket import obsws, events, requests
import logging

LOGGER: logging.Logger = logging.getLogger("OBS-Socket")

host = "localhost"
port = 4455
streamerbot_port = 4456
# password = ""
ws = None

alignments = {}
alignments["top-left"] = 5
alignments["top-center"] = 4
alignments["top-right"] = 6
alignments["center-left"] = 1
alignments["center"] = 0
alignments["center-right"] = 2
alignments["bottom-left"] = 9
alignments["bottom"] = 8
alignments["bottom-right"] = 10


def on_event(message):
    print("Got message {}".format(message))


def on_switch(message):
    print("You changed the scene to {}".format(message.getSceneName()))


def connect():
    global ws
    print("Setting up websocket.")
    ws = obsws(host, port)
    ws.register(on_event)
    ws.register(on_switch, events.SwitchScenes)
    ws.register(on_switch, events.CurrentProgramSceneChanged)
    ws.connect()


def disconnect():
    global ws
    if ws is not None:
        ws.disconnect()
        print("websocket was disconnected!")
    else:
        print("websocket was never connected... hopefully?")


def get_source_transform(scene_name=None, source_name=str):
    global ws

    if scene_name is None:
        scene_name = get_scene_by_source_name(source_name)
        if scene_name is None:
            LOGGER.error(f"Source {source_name} not found in any scene.")
            return None

    response = ws.call(
        requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name)
    )
    myItemID = response.datain["sceneItemId"]
    response = ws.call(
        requests.GetSceneItemTransform(sceneName=scene_name, sceneItemId=myItemID)
    )
    transform = {}
    transform["positionX"] = response.datain["sceneItemTransform"]["positionX"]
    transform["positionY"] = response.datain["sceneItemTransform"]["positionY"]
    transform["scaleX"] = response.datain["sceneItemTransform"]["scaleX"]
    transform["scaleY"] = response.datain["sceneItemTransform"]["scaleY"]
    transform["rotation"] = response.datain["sceneItemTransform"]["rotation"]
    transform["sourceWidth"] = response.datain["sceneItemTransform"][
        "sourceWidth"
    ]  # original width of the source
    transform["sourceHeight"] = response.datain["sceneItemTransform"][
        "sourceHeight"
    ]  # original width of the source
    transform["width"] = response.datain["sceneItemTransform"][
        "width"
    ]  # current width of the source after scaling, not including cropping. If the source has been flipped horizontally, this number will be negative.
    transform["height"] = response.datain["sceneItemTransform"][
        "height"
    ]  # current height of the source after scaling, not including cropping. If the source has been flipped vertically, this number will be negative.
    transform["cropLeft"] = response.datain["sceneItemTransform"][
        "cropLeft"
    ]  # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
    transform["cropRight"] = response.datain["sceneItemTransform"][
        "cropRight"
    ]  # the amount cropped off the *original source width*. This is NOT scaled, must multiply by scaleX to get current # of cropped pixels
    transform["cropTop"] = response.datain["sceneItemTransform"][
        "cropTop"
    ]  # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
    transform["cropBottom"] = response.datain["sceneItemTransform"][
        "cropBottom"
    ]  # the amount cropped off the *original source height*. This is NOT scaled, must multiply by scaleY to get current # of cropped pixels
    transform["alignment"] = response.datain["sceneItemTransform"]["alignment"]

    # Fetch scene specifications
    response = ws.call(requests.GetVideoSettings())
    transform["sceneWidth"] = response.datain["baseWidth"]
    transform["sceneHeight"] = response.datain["baseHeight"]
    transform["length"] = transform["sceneWidth"]
    return transform


# The transform should be a dictionary containing any of the following keys with corresponding values
# positionX, positionY, scaleX, scaleY, rotation, width, height, sourceWidth, sourceHeight, cropTop, cropBottom, cropLeft, cropRight
# e.g. {"scaleX": 2, "scaleY": 2.5}
# Note: there are other transform settings, like alignment, etc, but these feel like the main useful ones.
# Use get_source_transform to see the full list
def set_source_transform(scene_name, source_name, new_transform):
    global ws
    response = ws.call(
        requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name)
    )
    myItemID = response.datain["sceneItemId"]
    ws.call(
        requests.SetSceneItemTransform(
            sceneName=scene_name, sceneItemId=myItemID, sceneItemTransform=new_transform
        )
    )


def center_horizontally(scene_name, source_name):
    global ws
    transform = get_source_transform(scene_name, source_name)

    # Update alignment to be centered horizontally based on its current vertical alignment.
    # Note: the original code had 'alignments["top"]' which is not defined, corrected to 'alignments["top-center"]'.
    match transform["alignment"]:
        case 9 | 8 | 10:
            transform["alignment"] = alignments["bottom"]
        case 1 | 0 | 2:
            transform["alignment"] = alignments["center"]
        case 5 | 4 | 6:
            transform["alignment"] = alignments["top-center"]
        case _:
            pass

    # Center the source horizontally in the scene.
    # Since we set the alignment to a horizontal center (8, 0, or 4), the target X position is simply the scene midpoint.
    transform["positionX"] = transform["sceneWidth"] / 2

    set_source_transform(scene_name, source_name, transform)


def center_vertically(scene_name, source_name):
    global ws
    transform = get_source_transform(scene_name, source_name)

    # Update alignment to be centered vertically based on its current horizontal alignment.
    match transform["alignment"]:
        case 5 | 1 | 9:
            transform["alignment"] = alignments["center-left"]
        case 4 | 0 | 8:
            transform["alignment"] = alignments["center"]
        case 6 | 2 | 10:
            transform["alignment"] = alignments["center-right"]
        case _:
            pass

    # Center the source vertically in the scene.
    # Since we set the alignment to a vertical center (1, 0, or 2), the target Y position is simply the scene midpoint.
    transform["positionY"] = transform["sceneHeight"] / 2

    set_source_transform(scene_name, source_name, transform)


def center(scene_name, source_name):
    global ws
    transform = get_source_transform(scene_name, source_name)

    # Set selection as center-aligned
    transform["alignment"] = alignments["center"]

    # Center both X and Y
    transform["positionX"] = transform["sceneWidth"] / 2
    transform["positionY"] = transform["sceneHeight"] / 2

    set_source_transform(scene_name, source_name, transform)


# Use dougdougs code as a reference
# https://github.com/DougDougGithub/ChatGodApp/blob/main/obs_websockets.py
def set_text(source_name, text):
    global ws
    ws.call(
        requests.SetInputSettings(inputName=source_name, inputSettings={"text": text})
    )


def set_image(source_name, file):
    global ws
    ws.call(
        requests.SetInputSettings(inputName=source_name, inputSettings={"file": file})
    )


def set_file(source_name, file):
    global ws
    ws.call(
        requests.SetInputSettings(inputName=source_name, inputSettings={"file": file})
    )


def get_scene_by_source_name(source_name):
    global ws
    response = ws.call(requests.GetSceneList())
    for scene in response.datain["scenes"]:
        response = ws.call(requests.GetSceneItemList(sceneName=scene["sceneName"]))
        for source in response.datain["sceneItems"]:
            if source["sourceName"] == source_name:
                return scene["sceneName"]
    return None


def get_source_by_name(scene_name, source_name):
    global ws
    response = ws.call(requests.GetSceneItemList(sceneName=scene_name))
    source = list(
        filter(
            lambda sceneItem: sceneItem["sourceName"] == source_name,
            response.datain["sceneItems"],
        )
    )[0]
    return source


def enable_source(scene_name, source_name):
    global ws
    source_to_enable = get_source_by_name(scene_name, source_name)
    source_to_enable_scene_id = source_to_enable["sceneItemId"]
    ws.call(
        requests.SetSceneItemEnabled(
            sceneName=scene_name,
            sceneItemId=source_to_enable_scene_id,
            sceneItemEnabled=True,
        )
    )


def disable_source(scene_name, source_name):
    global ws
    source_to_enable = get_source_by_name(scene_name, source_name)
    source_to_enable_scene_id = source_to_enable["sceneItemId"]
    ws.call(
        requests.SetSceneItemEnabled(
            sceneName=scene_name,
            sceneItemId=source_to_enable_scene_id,
            sceneItemEnabled=False,
        )
    )


def play_sound_effect(sound_effect_file):
    global ws
    ws.call(
        requests.TriggerMediaInputAction(
            inputName=sound_effect_file,
            mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
        )
    )
