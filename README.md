# OBS Python Control

Program to control OBS Websocket in Python. Basically just make it really easy to add onto stuff whether it's feature parity with something in Streamer.bot, or something weird I want to do.

## Major Components
* OBS Websocket

    Abstracts some of function event and request calls to OBS Websocket to make it easier to use.

* Twitch Bot

    Actual bot that connects to Twitch and listens to chat. Could probably program this to do more, but right now it just listens to chat.

* Matt Meme Generator

    A meme generator that uses the Twitch Bot to listen to chat for Matt's first time messages and then generates a meme with his message.

## Requirements
* Python 3.13.9
* venv
* obs-websocket-py
* twitchio
* aiofiles
* pygtail

## Websocket Portion

* [OBS Websocket Protocols](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#events)