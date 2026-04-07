import pygtail
import obssocket
import twitchio
import asyncio
import os
import time
import twitchbot
import logging
import glob
from random import randint

LOGGER: logging.Logger = logging.getLogger("Matt-Meme-Generator")
twitchio.utils.setup_logging(level=logging.INFO)

# Make this

# List of top and bottom text and image link.
MATT = [
    ("IM MATT", "I'M COOL", "matt.png"),
    ("ME WHEN THE", "HONDA CIVIC\nIS BLUE", "matt_thumbs_up.jpg"),
    ("ME WHEN THE", "HONDA CIVIC\nISN'T BLUE", "matt_thumbs_down.jpg"),
    ("SAD", "MATT", "matt_sad.png"),
    ("THE 3 STAGES", "OF MATT", "matt_matt_matt.png"),
]
MATT_HERE_TODAY = False

scene = "Overlay_MemeGenerator"
source_image = "dynamic_meme"
source_text_top = "dynamic_meme_top_text"
source_bottom_text = "dynamic_meme_bottom_text"


# Returns the latest chat log file in the directory.
def get_latest_chat_log():
    files = glob.glob("ChatLog/chat_log_*.txt")
    if not files:
        return None
    return max(files, key=os.path.getctime)


# Returns the full absolute path given a relative path of a file.
def get_full_path(relative_path):
    return os.path.abspath(relative_path)


# Returns the full absolute path to a matt image.
def get_matt_image_path(matt_file):
    return get_full_path("Matt/{}".format(matt_file))


def enable_random_matt_meme():
    # Create/Activate text with random image.
    overlay_scene = "Overlay_DynamicCombined"
    matt_scene = "Overlay_MemeGenerator"
    source_image = "dynamic_meme"
    source_text_top = "dynamic_meme_top_text"
    source_bottom_text = "dynamic_meme_bottom_text"

    try:
        obssocket.connect()

        matt_index = randint(0, len(MATT) - 1)
        # LOGGER.info(obssocket.get_source_transform(scene, source_image))
        obssocket.center(matt_scene, source_image)
        obssocket.set_file(source_image, get_matt_image_path(MATT[matt_index][2]))
        obssocket.set_text(source_text_top, MATT[matt_index][0])
        obssocket.set_text(source_bottom_text, MATT[matt_index][1])

        obssocket.enable_source(overlay_scene, matt_scene)
        time.sleep(60)
        obssocket.disable_source(overlay_scene, matt_scene)
        # time.sleep(1)
    except KeyboardInterrupt:
        pass
    obssocket.disconnect()


def watch_for_matt():
    global MATT_HERE_TODAY
    # 1. Find the latest chat log file.
    latest_log = get_latest_chat_log()
    latest_offset_log = "{}.matt_offset".format(latest_log)
    if not latest_log:
        LOGGER.info("No chat log found.")
        return

    # 2. Read the latest chat log file.
    # 3. Watch for matt's username... which I forgot.
    # 4. If detected, we run enable_random_matt_meme().
    LOGGER.info(f"Watching {latest_log}...")
    while True:
        for line in pygtail.Pygtail(
            filename=latest_log,
            offset_file=latest_offset_log,
            save_on_end=True,
            paranoid=True,
        ):
            if not MATT_HERE_TODAY and (
                line.startswith("MattDoes_") or line.startswith("mateomeoteo")
            ):
                MATT_HERE_TODAY = True
                enable_random_matt_meme()


watch_for_matt()
