from markdown import markdown
from flask import Flask, render_template, current_app
import logging
import twitchio
import subprocess
import os
import time
import psutil
import threading
import json

LOGGER: logging.Logger = logging.getLogger("Dommy Mommy")
twitchio.utils.setup_logging(level=logging.INFO)
app = Flask(__name__)
python_path = "Scripts/python"

# Data structure that contins the name of the prorgam, relative path to the python file, and the process id.
programs = {
    "Test": {
        "url": "/test",
        "path": "test.py",
        "state": "stopped",
        "pid": None,
    },
    "Twitch Bot": {
        "url": "/twitch-bot",
        "path": "twitchbot.py",
        "state": "stopped",
        "pid": None,
    },
    "Tony Meme Generator": {
        "url": "/tony-meme-generator",
        "path": "tony-meme-generator.py",
        "state": "stopped",
        "pid": None,
    },
}


# Monitors the PID to update the state and the terminal output for the flask appliaction.
#
# Before this program is called, the checks if there is already a thread running or not.
# If there is, it will not start the program.
#
# Intended to run in a separate thread.
def start_and_monitor_program(program_name: str):
    programs[program_name]["pid"] = subprocess.Popen(
        [python_path, programs[program_name]["path"]]
    ).pid

    while True:
        time.sleep(5)

        # Check if flask application is still alive. If not, kill self.
        # Get process from the pid.
        try:
            process = psutil.Process(programs[program_name]["pid"])
        except psutil.NoSuchProcess:
            process = None

        # If the program is no longer running, update the state and break the loop.
        if current_app and process and process.is_running():
            programs[program_name]["state"] = "running"
        else:
            if not current_app:
                LOGGER.info(
                    f"Flask application is no longer alive. Killing program {program_name}"
                )
            elif not process or not process.is_running():
                LOGGER.info(f"Program {program_name} is no longer running.")

            programs[program_name]["state"] = "stopped"
            programs[program_name]["pid"] = None
            break


def stop_program(program_name: str):
    if program_name not in programs:
        raise ValueError(f"Program {program_name} not found.")

    program = programs[program_name]
    if program["state"] == "stopped":
        LOGGER.warning(f"Program {program_name} is not running. No need to kill.")
        return False

    LOGGER.info(f"Killing program {program_name}")
    psutil.Process(program["pid"]).terminate()
    return True


# Starts a program in a separate thread and assigns to programs dict.
#
# Returns True if the program was started successfully, False otherwise.
def launch_program_thread(program_name: str) -> bool:
    if program_name not in programs:
        raise ValueError(f"Program {program_name} not found.")

    program = programs[program_name]
    if program["state"] == "running":
        LOGGER.warning(f"Program {program_name} is already running.")
        return False

    threading.Thread(target=start_and_monitor_program, args=(program_name,)).start()
    return True


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/status", methods=["GET"])
def program_status():
    return json.dumps(programs)


# @app.route("/twitch-bot/start", methods=["POST"])
# def twitch_bot_start():
#     launch_program_thread("Test")
#     return "Twitch Bot Started"


# @app.route("/twitch-bot/stop", methods=["POST"])
# def twitch_bot_stop():
#     return "Twitch Bot Stopped"


# @app.route("/twitch-bot/restart", methods=["POST"])
# def twitch_bot_restart():
#     return "Twitch Bot Restarted"


@app.route("/tony-meme-generator/start", methods=["POST"])
def tony_meme_generator_start():
    launch_program_thread("Tony Meme Generator")
    return "Tony Meme Generator Started"


@app.route("/tony-meme-generator/stop", methods=["POST"])
def tony_meme_generator_stop():
    stop_program("Tony Meme Generator")
    return "Tony Meme Generator Stopped"


@app.route("/tony-meme-generator/restart", methods=["POST"])
def tony_meme_generator_restart():
    stop_program("Tony Meme Generator")
    time.sleep(1)
    launch_program_thread("Tony Meme Generator")
    return "Tony Meme Generator Restarted"


# Represent each of the main programs as separate boxes.
#
# First row has the name of the program.
# Second row has the status of the program (running or not).
# Third row has buttons to start, stop, and restart the program.
# Fourth row has the terminal output of the program.


# Kill all program when the flask app is closed.
# @app.teardown_appcontext
# def kill_all_programs(exception=None):
#     for program in programs:
#         stop_program(program)
