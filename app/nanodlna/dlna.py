#!/usr/bin/env python3
# encoding: UTF-8

import os
from os.path import exists

import pkgutil
import sys
from xml.sax.saxutils import escape as xmlescape

if sys.version_info.major == 3:
    import urllib.request as urllibreq
else:
    import urllib2 as urllibreq

import traceback
import logging
import json
import xmltodict

def send_dlna_action(device, data, action):
    logging.debug("Sending DLNA Action: {}".format(
        json.dumps({
            "action": action,
            "device": device,
            "data": data
        })
    ))

    action_data = pkgutil.get_data("app", f"nanodlna/templates/action-{action}.xml").decode("UTF-8")
    if data:
        action_data = action_data.format(**data)
    action_data = action_data.encode("UTF-8")

    headers = {
        "Content-Type": "text/xml; charset=\"utf-8\"",
        "Content-Length": "{0}".format(len(action_data)),
        "Connection": "close",
        "SOAPACTION": "\"{0}#{1}\"".format(device["st"], action)
    }

    logging.debug("Sending DLNA Request: {}".format(
        json.dumps({
            "url": device["action_url"],
            "data": action_data.decode("UTF-8"),
            "headers": headers
        })
    ))

    try:
        request = urllibreq.Request(device["action_url"], action_data, headers)
        with urllibreq.urlopen(request) as res:
            response = res.read()
            return response

    except Exception:
        logging.error("Unknown error sending request: {}".format(
            json.dumps({
                "url": device["action_url"],
                "data": action_data.decode("UTF-8"),
                "headers": headers,
                "error": traceback.format_exc()
            })
        ))
        return None


def play(files_urls, device, meta_data):

    logging.debug("Starting to play: {}".format(
        json.dumps({
            "files_urls": files_urls,
            "device": device
        })
    ))

    video_data = {
        "uri_video": files_urls["file_video"],
        "type_video": os.path.splitext(files_urls["file_video"])[1][1:],
    }

    #This has not been tested yet it may break seeking
    if "file_subtitle" in files_urls and files_urls["file_subtitle"]:
        video_data.update({
            "uri_sub": files_urls["file_subtitle"],
            "type_sub": os.path.splitext(files_urls["file_subtitle"])[1][1:]
        })

        metadata = pkgutil.get_data(
            "app",
            "nanodlna/templates/metadata-video_subtitle.xml").decode("UTF-8")
        video_data["metadata"] = xmlescape(metadata.format(**video_data))

    else:
        metadata = pkgutil.get_data(
            "app",
            "nanodlna/templates/metadata.xml").decode("UTF-8")
        video_data["metadata"] = xmlescape(metadata.format(**meta_data))

    logging.debug(f"Created video data: {json.dumps(video_data)}")


    send_dlna_action(device, video_data, "SetAVTransportURI")

    logging.debug("Playing video")
    send_dlna_action(device, video_data, "Play")

def resume(device):
    logging.debug("Pausing device: {}".format(
    json.dumps({
        "device": device
    })
))
    send_dlna_action(device, None, "Play")

def pause(device):
    logging.debug("Pausing device: {}".format(
        json.dumps({
            "device": device
        })
    ))
    send_dlna_action(device, None, "Pause")


def stop(device):
    logging.debug("Stopping device: {}".format(
        json.dumps({
            "device": device
        })
    ))
    send_dlna_action(device, None, "Stop")


def seek(device, target):
    logging.debug("Seeking device: {}".format(
        json.dumps({
            "device": device
        })
    ))
    send_dlna_action(device, target, "Seek")

def getPos(device):
    logging.debug("Finding Posistion: {}".format(
        json.dumps({
            "device": device
        })
    ))
    res = send_dlna_action(device, None, "GetPositionInfo")
    return xmltodict.parse(res)

def GetTransportInfo(device):
    logging.debug("Finding Posistion: {}".format(
        json.dumps({
            "device": device
        })
    ))
    res = send_dlna_action(device, None, "GetTransportInfo")
    return xmltodict.parse(res)
