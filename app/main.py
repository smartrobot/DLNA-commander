from plexapi.server import PlexServer
from starlette.websockets import WebSocket, WebSocketDisconnect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
from .nanodlna import dlna, devices
import urllib.parse
from pymediainfo import MediaInfo
import requests
import datetime
import json


#load settings
f = open('settings.json')
settings = json.load(f)
print(settings)
f.close()

app = FastAPI()

plex = PlexServer(settings["plex_baseurl"], settings["plex_token"])

movies = plex.library.section('Movies')

thumb_url = f'?checkFiles=1&includeAllConcerts=1&includeBandwidths=1&includeChapters=1&includeChildren=1&includeConcerts=1&includeExtras=1&includeFields=1&includeGeolocation=1&includeLoudnessRamps=1&includeMarkers=1&includeOnDeck=1&includePopularLeaves=1&includePreferences=1&includeRelated=1&includeRelatedCount=1&includeReviews=1&includeStations=1&X-Plex-token={settings["plex_token"]}'

class Play(BaseModel):
    title: str
    device: str
    file_path: str
    videoUrl: str

class Seek(BaseModel):
    device: str
    target: str

class Dev(BaseModel):
    device: str


# From https://github.com/tiangolo/fastapi/issues/258
class Notifier:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.generator = self.get_notification_generator()

    async def get_notification_generator(self):
        while True:
            message = yield
            await self._notify(message)

    async def push(self, msg: str):
        await self.generator.asend(msg)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def remove(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def _notify(self, message: str):
        living_connections = []
        while len(self.connections) > 0:
            # Looping like this is necessary in case a disconnection is handled
            # during await websocket.send_text(message)
            websocket = self.connections.pop()
            await websocket.send_text(message)
            living_connections.append(websocket)
        self.connections = living_connections


notifier = Notifier()

#Generate store for all plex items
libraryItems = []

#CORS
origins = [
    "*",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Websocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        notifier.remove(websocket)

#Create a notifier for the websockets
@app.on_event("startup")
async def startup():
    await notifier.generator.asend(None)

#Build library on startup
@app.on_event("startup")
async def build_library():
    for e,video in enumerate(movies.search()):
        libraryItems.append(
            {   
                'id':video.ratingKey,
                'title':video.title,
                'thumbUrl':f'{settings["plex_baseurl"]+video.thumb+thumb_url}',
                'summary':video.summary,
                'files':[]
            }
        )

        for media in video.media:
                for part in media.parts:
                    libraryItems[e]['files'].append(
                        {
                        "id":part.id,
                        "file":part.file,
                        "url":urllib.parse.quote(part.file).replace(settings["plex_moviePath"], settings["nginx_file_server_url"]),
                        }
                    )

@app.on_event("startup")
@repeat_every(seconds=1)
async def pushUpdate():
    #Push updates via websockets
    try:
        device = devices.register_device(settings["selected_device"])
        position = dlna.getPos(device)
        uri = position['s:Envelope']['s:Body']['u:GetPositionInfoResponse']['TrackURI']
        pos = position['s:Envelope']['s:Body']['u:GetPositionInfoResponse']['RelTime']
        TrackDuration = position['s:Envelope']['s:Body']['u:GetPositionInfoResponse']['TrackDuration']
        ts_info = dlna.GetTransportInfo(device)
        ts_status = ts_info['s:Envelope']['s:Body']['u:GetTransportInfoResponse']['CurrentTransportState']
        await notifier.push(str(json.dumps({'uri':uri, 'TrackDuration': TrackDuration, 'curtentPOS':pos, 'playback':ts_status})))
    except:
        pass #Error is in a seperate thread

@app.get("/")
async def root():
    return libraryItems

@app.post("/play")
async def play(play: Play):
    print(play.device)
    try:
        device = devices.register_device(play.device)
        dlna.stop(device) #Just send stop to what ever its doing actully checking is going to take longer

    except:
        return {"Error": "Could not connect to device"}
 
    #Build metadata
    try:
        media_info = MediaInfo.parse(play.file_path.replace(settings["plex_moviePath"], settings["local_movie_path"]))\
    
        video_tracks = []
        general_info = []
        for track in media_info.tracks:

            if track.track_type == "Video":
                video_tracks.append(track)
            elif track.track_type == "General":
                general_info.append(track)

        #Replace all illegal chars in title
        title = play.title.replace("&", "and")

        #create metadata dictionary
        meta_data = {
            "title": title,
            "duration" : datetime.timedelta(milliseconds=float(video_tracks[0].duration)),
            "file_size" : general_info[0].file_size,
            "width" : video_tracks[0].width,
            "height" : video_tracks[0].height,
            "bitrate" : video_tracks[0].bit_rate,
            "mimetype" : requests.head(play.videoUrl).headers['Content-Type'],
            "url": play.videoUrl
        }
    except:
        return {"error":"Could not parse mediainfo and build metadata"}

    #Play the requested File
    try:
        dlna.play({"file_video":play.videoUrl}, device, meta_data)
    except:
        return {"Error":"Could not start playback"}

    #return playing
    return { 'Playing' : 'true'}

@app.get("/devices")
async def findDevices():
    try:
        device = devices.get_devices()
        return device
    except:
        return {"Error":"Could not find devices"}

@app.post("/seek")
async def seek(seek: Seek):
    try:
        device = devices.register_device(seek.device)
        dlna.seek(device, {"target": seek.target})
        return {"seek":seek.target}

    except:
        return {"Error": f"Could not connect to device {seek.device}"}

@app.get("/getPos")
async def getPos(dev: Dev):
    try:
        device = devices.register_device(dev.device)
        data = dlna.getPos(device)
        return {'curtentPOS': data['s:Envelope']['s:Body']['u:GetPositionInfoResponse']['RelTime']}
    except:
        return {"Error": f"Could not connect to device {dev.device}"}

@app.get('/transportStatus')
async def getTransportStatus(dev: Dev):
    try:
        device = devices.register_device(dev.device)
        data = dlna.GetTransportInfo(device)
        return {'transportStatus': data['s:Envelope']['s:Body']['u:GetTransportInfoResponse']['CurrentTransportState']}
    except:
        return {"Error": f"Could not connect to device {dev.device}"}

@app.post('/playPause')
async def playPause(dev: Dev):
    try:
        device = devices.register_device(dev.device)
        data = dlna.GetTransportInfo(device)
        transportStatus = data['s:Envelope']['s:Body']['u:GetTransportInfoResponse']['CurrentTransportState']
    except:
        return {"Error": f"Could not connect to device {dev.device}"}
    #Press Play
    if transportStatus == 'PAUSED_PLAYBACK':
        try:
            dlna.resume(device)
            return {"Playing":True}
        except:
            return {"Error":"Could not press play"}

    #Press Puase
    elif transportStatus == 'PLAYING':
        try:
            dlna.pause(device)
            return {"Playing":False}
        except:
            return {"Error":"Could not press pause"}

    return {"Error":f"Something went wrong play/Pause transport status: {transportStatus}"}