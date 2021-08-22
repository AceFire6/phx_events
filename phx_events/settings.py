from environs import Env


env = Env()

PHX_WEBSOCKET_URL = env('PHX_WEBSOCKET_URL')
