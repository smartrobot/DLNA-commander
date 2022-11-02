# DLNA-commander

DLNA commander

# To do

Create docker for deployment

# Install
+ clone and build web ui https://github.com/smartrobot/DLNA-commander-UI

## Setup Nginx

Add these headers and mimetpyes to nginx.conf:
+ contentFeatures.dlna.org : DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000
+ transferMode.dlna.org : Streaming
+ Server : UPnP/1.0 DLNADOC/1.50 Platinum/1.0.5.13
+ add updated mimetypes (will update with proper config)

Create new site config
+ Add static UI build to / url
+ Add your movies directory as static files to /movies

## Fill out settings.json

### Plex api config

"plex_baseurl":"http://some-ip:32400" -- The url/ip of your plex server

"plex_token" : "-token-" --get your token using these instructions https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### File mapping config

"local_movie_path" : "/mnt/mymovies" --The path to your movies on the machine you are running this server on

"plex_moviePath" :"/mymovies" -- The path to your movies that the plex server is on

### The root url of your movies served by nginx

"nginx_file_server_url" : "http://someIP:somePort/movies",

### The url to your dlna device control xml

"selected_device" : "http://someIP:Someport/somefile.xml"

## Instal deps

+ Install pipenv
+ pipenv install

## Run
pipenv shell 

python dev_server.py

or

pipenv run python dev_server.py