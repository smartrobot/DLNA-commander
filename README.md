# DLNA-commander

DLNA commander

# To do

Create docker for deployment

## Setup Nginx

Add these headers and mimetpyes to nginx.conf:
+ some header (will update with proper config)
+ Some header (will update with proper config)
+ add updated mimetypes (will update with proper config)

Create new site config
+ Add static UI build to / url
+ Add your movies directory as static files to /movies

## fill out settings.json

### Plex api config

"plex_baseurl":"http://some-ip:32400", -- The url/ip of your plex server

"plex_token" : "", --get your token using these instructions https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### File mapping config

"local_movie_path" : "", --The path to your movies on the machine you are running this server on

"plex_moviePath" :"", -- The path to your movies that the plex server is on

### The root url of your movies served by nginx

"nginx_file_server_url" : "someIP:somePort/movies",

### The url to your dlna device

"selected_device" : ""

## Instal deps

Install pipenv

pipenv install

## Run

pipenv python dev_server.py