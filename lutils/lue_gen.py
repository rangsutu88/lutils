# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os, sys, time, re, socket, socks, threading, random, gzip, datetime, httplib, logging, traceback
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
from lutils.socksipyhandler import SocksiPyHandler, SocksiPysHandler

from lutils import read_random_lines, LUTILS_ROOT


__all__ = ['LRequest', 'LRequestCookie']

#socket.setdefaulttimeout(200)

logger = logging.getLogger('lutils')

NOT_REQUEST_CODE = [404, ]



header_path = os.path.join(LUTILS_ROOT, 'header')
USER_AGENT_DIR = os.path.join(LUTILS_ROOT, 'user_agent')

def generator_header():
    user_agent = read_random_lines(USER_AGENT_DIR, 5)[0]

    return [('User-Agent', user_agent),
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
    ('Accept-Language', 'en-us,en;q=0.7,zh-cn;q=0.3'),
    ('Accept-Encoding', 'gzip,deflate'),
    ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
    ('Connection', 'keep-alive')]


class LCookieJar():
    def _cookie_from_cookie_tuple(self, tup, request):
        name, value, standard, rest = tup

        domain = standard.get("domain", Absent)
        path = standard.get("path", Absent)
        port = standard.get("port", Absent)
        expires = standard.get("expires", Absent)

        # set the easy defaults
        version = standard.get("version", None)
        if version is not None:
            try:
                version = int(version)
            except ValueError:
                return None  # invalid version, ignore cookie
        secure = standard.get("secure", False)
        # (discard is also set if expires is Absent)
        discard = standard.get("discard", False)
        comment = standard.get("comment", None)
        comment_url = standard.get("commenturl", None)

        # set default path
        if path is not Absent and path != "":
            path_specified = True
            path = escape_path(path)
        else:
            path_specified = False
            path = request_path(request)
            i = path.rfind("/")
            if i != -1:
                if version == 0:
                    # Netscape spec parts company from reality here
                    path = path[:i]
                else:
                    path = path[:i+1]
            if len(path) == 0: path = "/"

        # set default domain
        domain_specified = domain is not Absent
        # but first we have to remember whether it starts with a dot
        domain_initial_dot = False
        if domain_specified:
            domain_initial_dot = bool(domain.startswith("."))
        if domain is Absent:
            req_host, erhn = eff_request_host(request)
            domain = erhn
        elif not domain.startswith("."):
            domain = "."+domain

        # set default port
        port_specified = False
        if port is not Absent:
            if port is None:
                # Port attr present, but has no value: default to request port.
                # Cookie should then only be sent back on that port.
                port = request_port(request)
            else:
                port_specified = True
                port = re.sub(r"\s+", "", port)
        else:
            # No port attr present.  Cookie can be sent back on any port.
            port = None

        # set default expires and discard
        if expires is Absent:
            expires = None
            discard = True
        elif expires <= self._now:
            expires = self._now + 3600

        return Cookie(version,
            name, value,
            port, port_specified,
            domain, domain_specified, domain_initial_dot,
            path, path_specified,
            secure,
            expires,
            discard,
            comment,
            comment_url,
            rest)


class DumpCookieJar(LCookieJar, cookiejar.CookieJar):
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_cookies_lock']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self._cookies_lock = threading.RLock()



class LMozillaCookieJar(LCookieJar, cookiejar.MozillaCookieJar):
    pass

def find_open_port(min_port=5000, max_port=10000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while 1:
        port = random.randint(min_port, max_port)
        try:
            s.bind(('127.0.0.1', port))
            s.close()
            del s
            return port
        except:
            time.sleep(0.5)
            port = port + random.randint(1, 300)

class LRequest(object):

    current_url = ''

    def __init__(self, string_proxy=None, request_header=None, timeout=90, debuglevel=0, **kwargs):
        self.debuglevel = debuglevel
        if self.debuglevel > 0:
            logger.info('%s: %s %s: begin init' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))

        handers = kwargs.get('handers', [])

        self._timeout = timeout
        self._body = ''
        self._opener = None
        self.tree = None

        if string_proxy:
            urlinfo = urlparse.urlparse(string_proxy)
            if urlinfo.scheme == 'ssh':
            # TODO ssh tunnel open
#                if self.tunnel.login(urlinfo.hostname, urlinfo.username, urlinfo.password, port=urlinfo.port, proxyport=localprot):
#                    socksiPyHandler = SocksiPyHandler(proxyargs=(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', localprot, True, None, None), debuglevel=debuglevel)
#                    socksiPysHandler = SocksiPysHandler(proxyargs=(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', localprot, True, None, None), debuglevel=debuglevel)
                pass
            elif urlinfo.scheme == 'socks5':
                socksiPyHandler = SocksiPyHandler(proxyargs=(socks.PROXY_TYPE_SOCKS5, urlinfo.hostname, urlinfo.port, True, urlinfo.username, urlinfo.password), debuglevel=debuglevel)
                socksiPysHandler = SocksiPysHandler(proxyargs=(socks.PROXY_TYPE_SOCKS5, urlinfo.hostname, urlinfo.port, True, urlinfo.username, urlinfo.password), debuglevel=debuglevel)
            elif urlinfo.scheme == 'socks4':
                socksiPyHandler = SocksiPyHandler(proxyargs=(socks.PROXY_TYPE_SOCKS4, urlinfo.hostname, urlinfo.port, True, urlinfo.username, urlinfo.password), debuglevel=debuglevel)
                socksiPysHandler = SocksiPysHandler(proxyargs=(socks.PROXY_TYPE_SOCKS4, urlinfo.hostname, urlinfo.port, True, urlinfo.username, urlinfo.password), debuglevel=debuglevel)
            elif urlinfo.scheme == 'http':
                socksiPyHandler = SocksiPyHandler(debuglevel=debuglevel)
                socksiPysHandler = SocksiPysHandler(debuglevel=debuglevel)
                httpProxyHandler = urllib2.ProxyHandler({'http': string_proxy})
                handers.append(httpProxyHandler)

        else:
            socksiPyHandler = SocksiPyHandler(debuglevel=debuglevel)
            socksiPysHandler = SocksiPysHandler(debuglevel=debuglevel)

        handers.append(socksiPyHandler)
        handers.append(socksiPysHandler)

        self.init_opener(request_header, handers)

        if self.debuglevel > 0:
            logger.info('%s: %s %s: end init' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))

    def write_log(self, l):
        if hasattr(self, 'f') and self.f:
            open(self.f, 'a').write('%s\n' % l)

    def init_opener(self, request_header=None, handers=[]):
        self.cookie = DumpCookieJar()
        handers.append(urllib2.HTTPCookieProcessor(self.cookie))

        self._opener = urllib2.build_opener(*handers)
        self._opener.addheaders = generator_header()

#            [('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0'),
#            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
#            ('Accept-Language', 'en-us,en;q=0.7,zh-cn;q=0.3'),
#            ('Accept-Encoding', 'gzip,deflate'),
#            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
#            ('Connection', 'keep-alive'), ]

        if os.path.exists(header_path):
            header = []
            headerFile = open(header_path, 'r').read()
            headerFile = '\n'.join([x for x in headerFile.split("\n") if x.strip() != ''])
            headerList = filter(lambda x: len(x.strip()) > 0, filter(None, headerFile.split('#')))
            headerContent = random.choice(headerList)
            header_lines = headerContent.splitlines()
            for header_line in header_lines:
                if len(header_line.strip()) > 0:
                    header_key, header_value = header_line.strip().split(':', 1)
                    header.append((header_key.strip(), header_value.strip()))
            self._opener.addheaders = header

        if request_header:
            self._opener.addheaders = request_header



    def open(self, url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, append_header=[], isdecode=False, repeat=3, is_xpath=True):
        try:
            self._body = ''
            if self.debuglevel > 0:
                logger.info('%s: %s %s: begin open' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))
            if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
                timeout = self._timeout
            if isinstance(url, basestring):
                url = url.replace(' ', '%20')
                and_reg = re.compile('&amp;')
                while len(re.findall(and_reg, url)) > 0:
                    url = url.replace('&amp;', '&')

            for header in append_header:
                self._opener.addheaders.append(header)

            if self.debuglevel > 0:
                for h in self._opener.addheaders:
                    logger.info('lutils header: %s' % (str(h)))
            while True:
                try:
                    if self.debuglevel > 0:
                        logger.info('%s: %s %s: begin opener open' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))
                    response = None
                    if data:
                        response = self._opener.open(url, data=urllib.urlencode(data, doseq=True), timeout=timeout) # data: {'name': 'value'}
                    else:
                        response = self._opener.open(url, timeout=timeout)

                    self.current_url = response.geturl()
                    self.body = response, isdecode, is_xpath
                    return response
                except (urllib2.HTTPError, urllib2.URLError, httplib.BadStatusLine, socket.timeout, socket.error, IOError, httplib.IncompleteRead, socks.ProxyConnectionError, socks.SOCKS5Error) as e:
                    repeat = repeat - 1
                    if isinstance(e, urllib2.HTTPError):
                        if e.code in NOT_REQUEST_CODE:
                            raise
                    time.sleep(random.randrange(10, 30))
                    if not repeat:
                        raise
                finally:
                    if self.debuglevel > 0:
                        logger.info('%s: %s %s: end opener open' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))
                    if response:
                        del response
        except :
            raise
        finally:
            if self.debuglevel > 0:
                logger.info('%s: %s %s: end open' % (datetime.datetime.now().isoformat(), os.getpid(), id(self)))

            for header in append_header:
                self._opener.addheaders.remove(header)

    def load(self, url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, append_header=[], isdecode=False, repeat=3, is_xpath=True):
        try:
            if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
                timeout = self._timeout
            return self.open(url, data, timeout, append_header, isdecode, repeat, is_xpath)
        except :
            if self.debuglevel:
                logger.error(traceback.format_exc())
            raise

    def load_file(self, file_path):
        self.loads(open(file_path, 'r').read())

    def loads(self, page_str, url=''):
        self.current_url = url
        self.body = page_str, '', True


    def getForms(self, url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, isdecode=False, repeat=3, is_xpath=False):
        return self.get_forms_by_url(url, data, timeout, isdecode, repeat, is_xpath)

    def get_forms_by_url(self, url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, isdecode=False, repeat=3, is_xpath=False):
        try:
            if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
                timeout = self._timeout
            response = None
            response = self.open(url, data, timeout, isdecode, repeat, is_xpath)
            return ParseFile(io.StringIO(str(BeautifulSoup(self.body, 'lxml')).replace('<br/>', '').replace('<hr/>', '')), response.geturl(), backwards_compat=False)
        except:
            raise
        finally:
            if response:
                del response

    def get_forms(self):
        return ParseFile(io.StringIO(str(BeautifulSoup(self.body, 'lxml')).replace('<br/>', '').replace('<hr/>', '')), self.current_url, backwards_compat=False)

    def getBody(self):
        return self._body

    def setBody(self, params):
        try:
            response, isdecode, is_xpath = params
            body = ''
            self._body = ''
            if isinstance(response, urllib.addinfourl):
                if response.info().get('Content-Encoding') in ('gzip', 'x-gzip'):
                    body = gzip.GzipFile('', 'r', 0, io.StringIO(response.read())).read()
                else:
                    body = response.read()

                if isdecode:
                    content_type = response.info().get('Content-Type', '')
                    charset = None
                    if content_type.find('charset=') > -1:
                        charset = content_type[content_type.find('charset=') + 8:]
                    if charset:
                        self._body = body.decode(charset, 'ignore')
                    else:
                        self._body = body
                else:
                    self._body = body
            else:
                self._body = response

            if is_xpath:
                # self.tree = Selector(text=str(BeautifulSoup(self.body, 'lxml')))
                # self.tree = html.fromstring(str(BeautifulSoup(self.body, 'lxml')))
                self.tree = html.fromstring(self.body)
        except :
            raise
        finally:
            del response
            del body

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

#    def css(self, css):
#        return self.tree.css(css)

    def get_ele_text(self, ele):
        return "".join([x for x in ele.itertext()]).strip()

    def __del__(self):
        if self._opener:
            del self._opener
        del self._body
        del self._timeout

class LRequestMozillaCookie(LRequest):

    def __init__(self, request_header=None, string_proxy=None, timeout=90, cookie_path=None, debuglevel=0, **kwargs):
        self.cookie_path = cookie_path

        super(LRequestMozillaCookie, self).__init__(request_header=request_header, string_proxy=string_proxy, timeout=timeout, debuglevel=0, **kwargs)

    def init_opener(self, request_header=None, handers=[]):
        self.cookie = LMozillaCookieJar(self.cookie_path)
        handers.append(urllib2.HTTPCookieProcessor(self.cookie))

        self._opener = urllib2.build_opener(*handers)
        self._opener.addheaders = generator_header()

#            [('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0'),
#            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
#            ('Accept-Language', 'en-us,en;q=0.7,zh-cn;q=0.3'),
#            ('Accept-Encoding', 'gzip,deflate'),
#            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
#            ('Connection', 'keep-alive'), ]

        if os.path.exists(header_path):
            header = []
            headerFile = open(header_path, 'r').read()
            headerFile = '\n'.join([x for x in headerFile.split("\n") if x.strip() != ''])
            headerList = filter(lambda x: len(x.strip()) > 0, filter(None, headerFile.split('#')))
            headerContent = random.choice(headerList)
            header_lines = headerContent.splitlines()
            for header_line in header_lines:
                if len(header_line.strip()) > 0:
                    header_key, header_value = header_line.strip().split(':', 1)
                    header.append((header_key.strip(), header_value.strip()))
            self._opener.addheaders = header

        if request_header:
            self._opener.addheaders = request_header

    def save_cookies(self):
        if self.cookie_path:
            self.cookie.save()

    def load_cookies(self):
        if self.cookie_path and os.path.exists(self.cookie_path):
            self.cookie.load()

LRequestCookie = LRequestMozillaCookie


import lud

def lencrypt(s):
    import base64, string
    from Crypto.Cipher import AES
    from binascii import b2a_hex

    cryptor = AES.new(''.join(['U', 's', 'e', 'r', 's', ' ', 'O', 'r', ' ', 'C', 'u', 's', 't', 'o', 'm', 's']), AES.MODE_CBC, ''.join(['G', 'i', 'r', 'l', 's', ' ', 'A', 'n', 'd', ' ', 'W', 'o', 'm', 'e', 'n', 's',]))

    ss = base64.b64encode(s)
    sss = []
    for _ in ss:
        sss.append(random.choice(string.printable))
        sss.append(_)
        sss.append(random.choice(string.printable))

    sss = ''.join(sss)

    b = random.randrange(10,30)
    a = random.randrange(10,30)

    _str = string.ascii_letters + string.digits + '''~!@#$%^&*()_+`-='''
    _bs = [random.choice(string.printable) for i in range(b)]
    _as = [random.choice(string.printable) for i in range(a)]

    _bs[3] = str(b)[0]
    _bs[8] = str(b)[1]

    _as[-3] = str(a)[0]
    _as[-8] = str(a)[1]

    sss = '%s%s%s' % (''.join(_bs), sss, ''.join(_as))
    text = base64.b64encode(sss)

    length = 16
    count = len(text)
    add = length - (count % length)
    text = text + ('\0' * add)
    return b2a_hex(cryptor.encrypt(text))


def lll(s):
    import base64, string
    from Crypto.Cipher import AES
    from binascii import b2a_hex

    cryptor = AES.new(''.join(['U', 's', 'e', 'r', 's', 'B', 'O', 'r', 'A', 'C', 'u', 's', 't', 'o', 'm', 's']), AES.MODE_CBC, ''.join(['G', 'i', 'r', 'l', 's', 'C', 'A', 'n', 'd', 'D', 'W', 'o', 'm', 'e', 'n', 's',]))

    ss = base64.b64encode(s)
    sss = []
    for _ in ss:
        sss.append(random.choice(string.printable))
        sss.append(_)
        sss.append(random.choice(string.printable))

    sss = ''.join(sss)

    b = random.randrange(10,30)
    a = random.randrange(10,30)

    _str = string.ascii_letters + string.digits + '''~!@#$%^&*()_+`-='''
    _bs = [random.choice(string.printable) for i in range(b)]
    _as = [random.choice(string.printable) for i in range(a)]

    _bs[3] = str(b)[0]
    _bs[8] = str(b)[1]

    _as[-3] = str(a)[0]
    _as[-8] = str(a)[1]

    sss = '%s%s%s' % (''.join(_bs), sss, ''.join(_as))
    text = base64.b64encode(sss)

    length = 16
    count = len(text)
    add = length - (count % length)
    text = text + ('\0' * add)
    return b2a_hex(cryptor.encrypt(text))






# if __name__ == '__main__':
##    lr = LRequestCookie(cookie_path='d:\\cc.cookies')
#    lr = LRequest()
#    f = lr.getForms('http://mail.163.com/')[0]
#
#    f['username'] = 'xt_master'
#    f['password'] = 'xt330300364'
#    lr.load(f.click())
#
##    lr.save_cookies()

#    generator_header()

#    lr = LRequest()
#    lr.load('http://www.baidu.com')
#    print lr.body







