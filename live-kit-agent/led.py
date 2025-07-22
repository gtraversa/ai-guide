import apa102
import time
import threading
try:
    import queue as Queue
except ImportError:
    import Queue as Queue


class Pixels:
    PIXELS_N = 3

    def __init__(self):
        self.brightness_scale = 0.5  # 50% brightness

        self.colors = [0] * 3 * self.PIXELS_N
        self.dev = apa102.APA102(num_led=self.PIXELS_N)

        self.next = threading.Event()
        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def wakeup(self, direction=0):
        def f():
            self._wakeup(direction)
        self.next.set()
        self.queue.put(f)

    def listen(self):
        self.next.set()
        self.queue.put(self._listen)

    def think(self):
        self.next.set()
        self.queue.put(self._think)

    def speak(self):
        self.next.set()
        self.queue.put(self._speak)

    def off(self):
        self.next.set()
        self.queue.put(self._off)

    def _run(self):
        while True:
            func = self.queue.get()
            func()

    def _wakeup(self, direction=0):
        for i in range(1, 25):
            red = int(255 * i / 24 * self.brightness_scale)
            colors = [red, 0, 0] * self.PIXELS_N
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _listen(self):
        green = int(255 * self.brightness_scale)
        colors = [0, green, 0] * self.PIXELS_N
        self.write(colors)
        self.colors = colors

    def _think(self):
        self.next.clear()
        while not self.next.is_set():
            for i in range(0, 25):
                green = int(255 * i / 24 * self.brightness_scale)
                colors = [0, green, 0] * self.PIXELS_N
                self.write(colors)
                time.sleep(0.01)
            for i in range(24, -1, -1):
                green = int(255 * i / 24 * self.brightness_scale)
                colors = [0, green, 0] * self.PIXELS_N
                self.write(colors)
                time.sleep(0.01)
        self.colors = colors

    def _speak(self):
        self.next.clear()
        while not self.next.is_set():
            for i in range(0, 25):
                red = int(255 * i / 24 * self.brightness_scale)
                blue = int(180 * i / 24 * self.brightness_scale)
                colors = [red, 0, blue] * self.PIXELS_N
                self.write(colors)
                time.sleep(0.01)
            for i in range(24, -1, -1):
                red = int(255 * i / 24 * self.brightness_scale)
                blue = int(180 * i / 24 * self.brightness_scale)
                colors = [red, 0, blue] * self.PIXELS_N
                self.write(colors)
                time.sleep(0.01)
        self.colors = colors

    def _off(self):
        self.write([0] * 3 * self.PIXELS_N)

    def write(self, colors):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(colors[3*i]), int(colors[3*i + 1]), int(colors[3*i + 2]))
        self.dev.show()
