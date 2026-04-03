import obssocket
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

LOGGER: logging.Logger = logging.getLogger("Tony-Meme-Generator")

overlay_scene = "Overlay_DynamicCombined"
scene = "Overlay_TonyMemeGenerator"
source_text_top = "dynamic_tony_meme_top_text"
source_bottom_text = "dynamic_tony_meme_bottom_text"
source_meme_enable_sfx = "Tony Meme SFX Stardew"


# Returns the latest chat log file in the directory.
def get_latest_redeem_log():
    files = glob.glob("ChatLog/redeem_*.txt")
    if not files:
        return None
    return max(files, key=os.path.getctime)


# Returns the full absolute path given a relative path of a file.
def get_full_path(relative_path):
    return os.path.abspath(relative_path)


async def set_and_enable_tony_meme(message_top, message_bottom):
    try:
        obssocket.connect()
        obssocket.set_text(source_text_top, message_top)
        obssocket.set_text(source_bottom_text, message_bottom)
        LOGGER.info("Enabling Tony Meme!")
        obssocket.enable_source(overlay_scene, scene)
        obssocket.play_sound_effect(source_meme_enable_sfx)
        time.sleep(30)
        LOGGER.info("Disabling Tony Meme!")
        obssocket.disable_source(overlay_scene, scene)
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    obssocket.disconnect()


# Watch for tony meme redemptions in redeem log.
#
# Defined as an async function to allow for await calls.
async def watch_for_tony_meme():
    # 1. Find the latest chat log file.
    latest_log = get_latest_redeem_log()
    latest_offset_log = "{}.tony_offset".format(latest_log)
    if not latest_log:
        LOGGER.info("No redeem log found.")
        return

    # 2. Read the latest chat log file.
    # 3. Watch for matt's username... which I forgot.
    # 4. If detected, we run set_and_enable_tony_meme().
    LOGGER.info(f"Watching {latest_log}...")
    while True:
        for line in pygtail.Pygtail(
            filename=latest_log,
            offset_file=latest_offset_log,
            save_on_end=True,
            paranoid=True,
        ):
            if line.startswith("Tony Meme"):
                split_line = line.split(";")
                message = split_line[2]
                message_split = message.split("\\\\")
                # Stripping messages of whitespace or new lines.
                top_message_text = message_split[0].strip()
                bottom_message_text = (
                    message_split[1].strip() if len(message_split) > 1 else ""
                )
                await set_and_enable_tony_meme(top_message_text, bottom_message_text)


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        await watch_for_tony_meme()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()
