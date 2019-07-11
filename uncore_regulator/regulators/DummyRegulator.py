import logging


class DummyRegulator():
    def __init__(self):
        pass

    def regulate(self, data):
        logging.info("[DummyRegulator] {}".format(data))
