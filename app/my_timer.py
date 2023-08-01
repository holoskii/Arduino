import time

class Timer:
    verbose: bool = True
    start_time: float

    def start(self):
        self.start_time = time.time()

    def stop(self, name):
        end_time: float = time.time()
        elapsed_time: float = (end_time - self.start_time) * 1000
        if self.verbose:
            print(f"{elapsed_time:3.0f} ms taken by {name}")

    def __init__(self):
        self.start()
