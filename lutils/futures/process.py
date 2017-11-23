# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

try:
    import queue
except ImportError:
    import Queue as queue

from concurrent.futures.process import ProcessPoolExecutor

class LProcessPoolExecutor(ProcessPoolExecutor):

    def __init__(self,  max_workers=10, maxsize=50, *args, **kwargs):
        super(ProcessPoolExecutor, self).__init__(max_workers=max_workers, *args, **kwargs)

#        self._work_queue = queue.Queue(maxsize=maxsize)