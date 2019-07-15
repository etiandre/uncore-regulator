import logging
import subprocess
from enum import Enum


class Phase(Enum):
    UNK = 0
    CPU = 1
    MEM = 2


class State(Enum):
    ADJUSTING = 0
    STABLE = 1


class SimpleRegulator():
    def __init__(self):
        # (min, max, step)
        self.freqs = (1.2, 2.7, 0.1)
        self.maxflops = 0
        self.phase = Phase.UNK
        self.state = State.ADJUSTING
        self.set_freq(None)
        self.cur_freq = None

    def reset(self):
        self.maxflops = 0
        self.state = State.ADJUSTING
        self.set_freq(None)

    def set_freq(self, f):
        if f:
            subprocess.run(
                ["likwid-setFrequencies", "--umin",
                 str(f), "--umax",
                 str(f)])
            logging.info("changed uncore freq to {}".format(f))
        else:
            subprocess.run(["likwid-setFrequencies", "--ureset"])
            logging.info("reset uncore freq limits")

    def tick(self, d):
        if d["flop/s"] < 10000:
            print("Not enough flop/s! Sleeping...")
            self.phase = Phase.UNK
        elif d["operational-intensity"] > 1 and self.phase != Phase.CPU:
            logging.info(
                "Detected CPU-intensive phase (operational intensity={})".
                format(d["operational-intensity"]))
            self.phase = Phase.CPU
            self.reset()
        elif d["operational-intensity"] < 1 and self.phase != Phase.MEM:
            logging.info(
                "Detected memory-intensive phase (operational intensity={})".
                format(d["operational-intensity"]))
            self.phase = Phase.MEM
            self.reset()

        if self.state == State.ADJUSTING and self.phase != Phase.UNK:
            if d["flop/s"] > self.maxflops:
                self._maxflops = d["flop/s"]
            elif d["flop/s"] > .98 * self.maxflops:
                # freq should go down
                self.cur_freq -= self.freqs[2]
                if self.cur_freq < self.freqs[0]: self.cur_freq = self.freqs[0]
                self.set_freq(self.cur_freq)
            else:
                # freq should go up
                self.cur_freq += self.freqs[2]
                if self.cur_freq > self.freqs[1]: self.cur_freq = self.freqs[1]
                self.set_freq(self.cur_freq)

        elif self.state == State.STABLE:
            pass
