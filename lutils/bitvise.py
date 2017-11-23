# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os
import time
import socket
import logging
import subprocess
import conf
from lutils import free_port


logger = logging.getLogger('lutils')

class SSHTimeout(Exception):
    pass

class AuthenticationError(Exception):
    pass

class StnlcNotExistError(Exception):
    pass

class Bitvise():

    _execute_cmd = 'stnlc.exe'

    def __init__(self, host, port, username='', password='', forwarding_ip='', forwarding_port=0, timeout=60, log_path=None): # 'stnlc.log'

        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.forwarding_ip = socket.gethostbyname(socket.gethostname()) if not forwarding_ip else '127.0.0.1'
        self.forwarding_port = free_port() if not forwarding_port else forwarding_port

        self.timeout = timeout
        self.popen = None
        self.log_path = open(log_path, "a+") if log_path is not None else subprocess.PIPE

    def start(self):
        if not os.path.exists(os.path.join(conf.BITVISE_HOME, self._execute_cmd)):
            raise StnlcNotExistError('Stnlc not Exist!!!')
        execute_cmd = '%s %s@%s:%s -pw=%s -proxyFwding=y -proxyListIntf=%s -proxyListPort=%s -proxyType=SOCKS5' % (
            os.path.join(conf.BITVISE_HOME, self._execute_cmd), self.username, self.host, self.port, self.password, self.forwarding_ip, self.forwarding_port)
        logger.info('SSH Forwarding: %s' % execute_cmd)

        # log_p = open(self.log_path, "a+") if self.log_path is not None else subprocess.STDOUT
        self.popen = subprocess.Popen(execute_cmd, stdin=subprocess.PIPE, stdout=self.log_path, stderr=self.log_path)
        # self.popen = subprocess.Popen(execute_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        t1 = time.time()

        while 1:
            line = self.popen.stdout.readline().strip()
            if line:
                logger.info(line)
                if line.find('Authentication completed') > -1:
                    break

                if line.find('Authentication failed') > -1:
                    raise AuthenticationError('Authentication Error!!!')

            if (time.time() - self.timeout) > t1:
                raise SSHTimeout('SSH Connection Timeout!!!')
            time.sleep(0.1)

        logger.info('SSH Forwarding Complete: (%s, %s)' % (self.forwarding_ip, self.forwarding_port))

        return (self.forwarding_ip, self.forwarding_port)

    def stop(self):

        if self.popen is not None:
            self.popen.kill()


    def __del__(self):
        self.stop()