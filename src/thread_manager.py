from threading import Thread


class DiscordThread(Thread):
    """
    Spawn the discord thread as a daemon with it's key
    """

    def __init__(self, name: str, target, key: str = None):
        Thread.__init__(self)
        self.name: str = name
        self.target = target
        self.key: str = key
        self.daemon = True

    def run(self):
        print(f"Launching {self.name}...")
        self.target(self.key)
