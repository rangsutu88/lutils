# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os, sys, time, re, socket, socks, threading, random, gzip, datetime, httplib, logging, requests # requesocks
if sys.version_info[0] >= 3:
    from http import cookiejar
    from urllib.parse import urlparse
    import io, urllib
else:
    import urlparse, urllib, urllib2
    import cookielib as cookiejar
    from cookielib import Absent, escape_path, request_path, eff_request_host, request_port, Cookie
    import StringIO as io


#from scrapy.selector import Selector
from lxml import html
from bs4 import BeautifulSoup
from ClientForm import ParseFile

from lutils import read_random_lines, LUTILS_ROOT


__all__ = ['LRequests']

#socket.setdefaulttimeout(200)

logger = logging.getLogger('lutils')

NOT_REQUEST_CODE = [404, ]

header_path = os.path.join(LUTILS_ROOT, 'header')
USER_AGENT_DIR = os.path.join(LUTILS_ROOT, 'user_agent')

def generator_header():
    user_agent = read_random_lines(USER_AGENT_DIR, 5)[0]

    return {'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.7,zh-cn;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Connection': 'keep-alive'}


class LRequests(object):
    def __init__(self, string_proxy=None, request_header=None, timeout=90, debuglevel=0, **kwargs):


        self.timeout = timeout
        self.headers = generator_header()

        # self.session = requesocks.session(headers=self.headers, timeout=timeout)
        self.session = requests.session()

#        self.session.headers = self.headers
        if string_proxy:
            self.session.proxies = {'http': string_proxy, 'https': string_proxy}


    def open(self, url, method='GET', data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, is_xpath=True, stream=False):

        response = self.session.request(method, url, data=data, timeout=self.timeout, allow_redirects=True) # , stream=stream
#        response = self.session.get(url, data=data, timeout=self.timeout, stream=stream)

        self.body = response, is_xpath, stream

        return response

    def load(self, url, method='GET', data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, is_xpath=True, stream=False):

        return self.open(url, method=method, data=data, timeout=timeout, is_xpath=is_xpath, stream=stream)

    def getForms(self, url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, is_xpath=False):
        try:
            if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
                timeout = self.timeout
            response = self.open(url, data=data, timeout=timeout, is_xpath=is_xpath)
            return ParseFile(io.StringIO(str(BeautifulSoup(self.body)).replace('<br/>', '').replace('<hr/>', '')), response.url, backwards_compat=False)
        except:
            raise


    def getBody(self):
        return self._body

    def setBody(self, params):
        try:
            response, is_xpath, stream = params


            self._body = ''
            if stream:
                self._body = response.raw
            else:
                self._body = response.text

            if is_xpath:
                self.tree = html.fromstring(str(BeautifulSoup(self.body)))
        except :
            raise

    def delBody(self):
        del self._body

    body = property(getBody, setBody, delBody, "http response text property.")

    def xpath(self, xpath):
        eles = self.tree.xpath(xpath)
        if eles and len(eles) > 0:
            return eles[0]

        return None


    def xpaths(self, xpath):
        return self.tree.xpath(xpath)


    def __del__(self):
        pass


if __name__ == '__main__':

#    l = LRequests(string_proxy='socks5://192.168.1.195:1072')
#     l = LRequests()
#     l.load('http://image.tiancity.com/article/UserFiles/Image/luoqi/2010/201009/29/3/4.jpg', is_xpath=False, stream=True)


#    print l.body

    # import shutil
    # shutil.copyfileobj(l.body, open('D:\\xxx.jpg', 'wb'))

    lr = LRequests(string_proxy='socks5://:@192.168.1.188:1080')
    lr.load('http://www.google.com')

    print lr.body

