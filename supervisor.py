import threading
from threading import Event

import importlib

import git

g = git.cmd.Git(".")

# Shared state
class BotState:
    def __init__(self):
        self.last_games = {}
        self.games_by_time = {}
        self.scheduled_tasks = {}

        self.reload_event = Event()

state = BotState()

def run_bot():
    import loserbot
    loserbot.run_bot(state)

def hotreload():
    g.pull()
    import loserbot
    importlib.reload(loserbot)
    loserbot.run_bot(state)

state.reload_callback = hotreload


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    while 1:
        state.reload_event.wait()
        state.reload_event.clear()
        
        hotreload()


