# DLNA-commander

DLNA commander

fill out settings.json

### Plex api config

"plex_baseurl":"http://some-ip:32400", -- The url/ip of your plex server

"plex_token" : "", --get your token using these instructions https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### File mapping config

"local_movie_path" : "", --The path to your movies on the machine you are running this server on

"plex_moviePath" :"", -- The path to your movies that the plex server is on

### The root url of your movies served by nginx

"nginx_file_server_url" : "",

### The url to your dlna device

"selected_device" : ""

Install pipenv

pipenv install

pipenv python dev_server.py