# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import threading

class LThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(LThread, self).__init__()
        self.stoped = False

    def stop(self):
        self.stoped = True