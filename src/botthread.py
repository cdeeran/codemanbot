import time
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


class GeneralTimerThread(Thread):
    def __init__(self, name: str, target, interval_secs: int):
        Thread.__init__(self)
        self.name: str = name
        self.target = target
        self.interval = interval_secs
        self.daemon = True

    def run(self):
        while True:
            self.target()
            time.sleep(self.interval)
