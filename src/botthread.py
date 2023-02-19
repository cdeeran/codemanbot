from threading import Thread


class BotThread(Thread):
    def __init__(self, name: str, target, key: str = None):
        Thread.__init__(self)
        self.name: str = name
        self.target = target
        self.key: str = key
        self.daemon = True

    def run(self):
        print(f"Launching {self.name}...")
        if self.key:
            self.target(self.key)
        else:
            self.target()
