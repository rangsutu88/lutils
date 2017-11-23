# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import logging
import traceback
import time
import threading
import weakref
try:
    import queue
except ImportError:
    import Queue as queue

from concurrent.futures.thread import ThreadPoolExecutor, _threads_queues
from concurrent.futures import _base

logger = logging.getLogger('lutils')

__all__ = ['LThreadPoolExecutor']

#def _worker(executor_reference, work_queue):
#    try:
#        while True:
#            try:
#                work_item = work_queue.get(block=False, timeout=1)
#                if work_item is not None:
#                    work_item.run()
#                    continue
#                executor = executor_reference()
#                if _shutdown or executor is None or executor._shutdown:
#                    work_queue.put(None)
#                    return
#                del executor
#            except queue.Empty:
#                time.sleep(0.5)
#    except BaseException:
#        _base.LOGGER.critical('Exception in worker', exc_info=True)


class LThreadPoolExecutor(ThreadPoolExecutor):

    def __init__(self,  max_workers=10, maxsize=50, *args, **kwargs):
        super(LThreadPoolExecutor, self).__init__(max_workers=max_workers, *args, **kwargs)

        self._work_queue = queue.Queue(maxsize=maxsize)


    def submit(self, fn, *args, **kwargs):
        try:
            return super(LThreadPoolExecutor, self).submit(fn, *args, **kwargs)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())


#    def _adjust_thread_count(self):
#        def weakref_cb(_, q=self._work_queue):
#            q.put(None)
#        if len(self._threads) < self._max_workers:
#            t = threading.Thread(target=_worker,
#                args=(weakref.ref(self, weakref_cb),
#                      self._work_queue))
#            t.daemon = True
#            t.start()
#            self._threads.add(t)
#            _threads_queues[t] = self._work_queue
