# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import time
import uuid
import gevent
import datetime
import croniter
import logging
import traceback
import random
import gc
from lutils.futures.thread import LThreadPoolExecutor
from lutils.futures.process import LProcessPoolExecutor

logger = logging.getLogger('lutils')

class Event(object):

    def __init__(self, command, tab, delay=0, event_id=None, *args, **kwargs):
        self.command = command
        self.event_id = event_id if event_id else uuid.uuid4().hex
        self.args = args
        self.kwargs = kwargs
        self.tab = tab

        now = datetime.datetime.now()
        self.cron = croniter.croniter(tab, now)

        self.delay = 0
        if delay > 0:
            self.delay = delay % 60

        self.set_next()

        self.debuglevel = kwargs.get('debuglevel', 0)

    def get_next(self):
        return self._next

    def set_next(self):
        self._next = time.mktime(self.cron.get_next(datetime.datetime).timetuple())
        if self.delay:
            self._next += (random.randrange(self.delay*1000) * 60) / 1000.0

    def update_cron(self, tab):
        now = datetime.datetime.now()
        self.cron = croniter.croniter(tab, now)
        self.tab = tab
        self.set_next()

    def matchtime(self, t1):
        if self.get_next() < t1:
            return True
        return False

    def check(self, executor):
        try:
            t = time.time()
            if self.matchtime(t):
                self.set_next()
                executor.submit(self.command, *self.args, **self.kwargs)
        except :
            logger.error(traceback.format_exc())


class CronTab(object):

    def __init__(self, *events):
        self.events = {}
        for _event in events:
            if _event.event_id in self.events: del self.events[_event.event_id]
            self.events[_event.event_id] = _event

    def _check(self):
        try:
            logger.info('check...')
            t1 = time.time()
            for event in self.events.values():
                gevent.spawn(event.check, self.executor)

            t1 += 60
            s1 = t1 - time.time()
            if gc.garbage:
                logger.error(gc.garbage)

            job = gevent.spawn_later(s1, self._check)
        except:
            logger.error(traceback.format_exc())

    def add_event(self, *events):
        for _event in events:
            if _event.event_id not in self.events.keys():
                self.events[_event.event_id] = _event

    def del_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]

    def get_event(self, event_id):
        if event_id in self.events:
            return self.events[event_id]

    def event_ids(self):
        return self.events.keys()

    def run(self):
        try:
            self._check()
            while True:
                gevent.sleep(60)
        except:
            logger.error(traceback.format_exc())


class CronTabThread(CronTab):

    def __init__(self, max_workers=10, *events):
        try:
            super(CronTabThread, self).__init__(*events)
            self.executor = LThreadPoolExecutor(max_workers=max_workers)
        except:
            logger.error(traceback.format_exc())

class CronTabProcess(CronTab):

    def __init__(self, max_workers=10, *events):
        super(CronTabProcess, self).__init__(*events)
        self.executor = LProcessPoolExecutor(max_workers=max_workers)


#def test_task():
#    print 'sdfsdf'
#
#cron = CronTab(
#    Event(test_task, '* * * * *'),
#)
#cron.run()