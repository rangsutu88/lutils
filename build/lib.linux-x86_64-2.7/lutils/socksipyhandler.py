# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os
import sys
import urllib2
import httplib
import socks
import socket
import datetime
import inspect
from urllib import addinfourl
from urllib2 import URLError

from lutils import LUTILS_ROOT

header_path = os.path.join(LUTILS_ROOT, 'mykey.pem')
header_path = os.path.join(LUTILS_ROOT, 'mykey.pub')

# proxyargs:  proxytype, addr, port, rdns=True, username, password
def create_connection(address, proxyargs=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, debuglevel=0):
    msg = "getaddrinfo returns an empty list"
    host, port = address
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socks.socksocket(af, socktype, proto)
            if proxyargs:
                sock.setproxy(*proxyargs)
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if debuglevel > 0:
                print('%s: %s begin connect %s %s %s %s %s' % (datetime.datetime.now(), os.getpid(), af, socktype, proto, canonname, sa))
            sock.connect(sa)
            if debuglevel > 0:
                print('%s: %s end connect %s %s %s %s %s' % (datetime.datetime.now(), os.getpid(), af, socktype, proto, canonname, sa))

            return sock

        except socket.error as msg:
            if sock is not None:
                sock.close()

    raise socket.error, msg


class SocksiPyConnection(httplib.HTTPConnection):
    def __init__(self, proxyargs=None, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        self.proxyargs = proxyargs

    def connect(self):
        self.sock = create_connection((self.host, self.port), self.proxyargs, self.timeout, debuglevel=self.debuglevel)# , self.source_address
        if self._tunnel_host:
            self._tunnel()

class SocksiPyHandler(urllib2.HTTPHandler):
    def __init__(self, debuglevel=0, *args, **kwargs):
        urllib2.HTTPHandler.__init__(self, debuglevel=debuglevel)
        self.args = args
        self.kw = kwargs

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=30):
            return SocksiPyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
        return self.do_open(build, req)


try:
    import ssl
except ImportError:
    pass
else:

    class SocksiPysConnection(httplib.HTTPSConnection):
        def __init__(self, proxyargs=None, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
            self.proxyargs = proxyargs

        def connect(self):
            sock = create_connection((self.host, self.port), self.proxyargs, self.timeout, debuglevel=self.debuglevel) # , self.source_address
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()

            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)

    class SocksiPysHandler(urllib2.HTTPSHandler):
        def __init__(self, debuglevel=0, *args, **kwargs):
            urllib2.HTTPSHandler.__init__(self, debuglevel=debuglevel)
            self.args = args
            self.kw = kwargs

        def https_open(self, req):
            def build(host, port=None, strict=None, timeout=30):
                return SocksiPysConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return self.do_open(build, req)
