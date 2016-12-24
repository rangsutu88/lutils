# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'

import os
import sys
import re
import time
import json
import copy
import shutil
import socket
import tempfile
import zipfile
import logging
import urlparse
import random
import traceback
import cPickle
import urllib2
import lxml
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.firefox import firefox_profile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.extension_connection import ExtensionConnection
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import NoSuchElementException

from lutils import read_random_lines, LUTILS_ROOT


USER_AGENT_DIR = os.path.join(LUTILS_ROOT, 'user_agent')
GECKODRIVER = os.path.join(LUTILS_ROOT, 'geckodriver')

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

logger = logging.getLogger('lutils')

class LFirefoxProfile(firefox_profile.FirefoxProfile):

    def __init__(self, profile_directory=None, is_temp=False):
        self.is_temp = is_temp
        if not firefox_profile.FirefoxProfile.DEFAULT_PREFERENCES:
            with open(os.path.join(os.path.dirname(firefox_profile.__file__), firefox_profile.WEBDRIVER_PREFERENCES)) as default_prefs:
                firefox_profile.FirefoxProfile.DEFAULT_PREFERENCES = json.load(default_prefs)

        self.default_preferences = copy.deepcopy(
            firefox_profile.FirefoxProfile.DEFAULT_PREFERENCES['mutable'])
        self.native_events_enabled = True
        self.profile_dir = profile_directory
        self.tempfolder = None
        if self.profile_dir is None:
            self.profile_dir = self._create_tempfolder()
        elif is_temp:
            self.tempfolder = tempfile.mkdtemp()
            newprof = os.path.join(self.tempfolder, "webdriver-py-profilecopy")
            shutil.copytree(self.profile_dir, newprof,
                ignore=shutil.ignore_patterns("parent.lock", "lock", ".parentlock"))
            self.profile_dir = newprof
            self._read_existing_userjs(os.path.join(self.profile_dir, "user.js"))

        self.extensionsDir = os.path.join(self.profile_dir, "extensions")
        self.userPrefs = os.path.join(self.profile_dir, "user.js")

        _ext_path = os.path.join(os.path.dirname(__file__), 'ext')
        addons = [os.path.join(_ext_path, a) for a in os.listdir(_ext_path)]
        for addon in addons:
            self.add_extension(addon)

    def _install_extension(self, addon, unpack=True):
        if addon == firefox_profile.WEBDRIVER_EXT:
            addon = os.path.join(os.path.dirname(firefox_profile.__file__), firefox_profile.WEBDRIVER_EXT)

        extensions_path = os.path.join(self.profile_dir, 'extensions')
        if not os.path.exists(extensions_path): os.makedirs(extensions_path)

        tmpdir = None
        xpifile = None
        if addon.endswith('.xpi'):
            tmpdir = tempfile.mkdtemp(suffix='.' + os.path.split(addon)[-1])
            compressed_file = zipfile.ZipFile(addon, 'r')
            for name in compressed_file.namelist():
                if name.endswith('/'):
                    _p = os.path.join(tmpdir, name)
                    if not os.path.exists(_p):
                        os.makedirs(_p)
                else:
                    if not os.path.isdir(os.path.dirname(os.path.join(tmpdir, name))):
                        os.makedirs(os.path.dirname(os.path.join(tmpdir, name)))
                    data = compressed_file.read(name)
                    with open(os.path.join(tmpdir, name), 'wb') as f:
                        f.write(data)
            xpifile = addon
            addon = tmpdir

            addon_details = self._addon_details(addon)
            addon_id = addon_details.get('id')
            assert addon_id, 'The addon id could not be found: %s' % addon

            xpi_path = os.path.join(extensions_path, '%s.xpi' % addon_id)
            if not os.path.exists(xpi_path):
                shutil.copy(xpifile, xpi_path)

            if tmpdir:
                try:
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except :
                    pass

class BrowserMixin():

    def sync_local(self):
        self.html = self.page_source

    def _clean(self, html, remove=['br', 'hr']):
        self.remove = remove
        html = re.compile('<!--.*?-->', re.DOTALL).sub('', html) # remove comments
        if remove:
            # XXX combine tag list into single regex, if can match same at start and end
            for tag in remove:
                html = re.compile('<' + tag + '[^>]*?/>', re.DOTALL | re.IGNORECASE).sub('', html)
                html = re.compile('<' + tag + '[^>]*?>.*?</' + tag + '>', re.DOTALL | re.IGNORECASE).sub('', html)
                html = re.compile('<' + tag + '[^>]*?>', re.DOTALL | re.IGNORECASE).sub('', html)
        return html

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, source):
        self._html = self._clean(source)
        self.tree = html.fromstring(self._html)

    def load(self, url):
        self.get(url)

    def scroll_down(self, click_num=5):
        body = self.xpath('//body')
        if body:
            for _ in range(click_num):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.1)
            time.sleep(1)

    def scroll_up(self, click_num=5):
        body = self.xpath('//body')
        if body:
            for _ in range(click_num):
                body.send_keys(Keys.PAGE_UP)
                time.sleep(0.1)
            time.sleep(1)

    def fill(self, name_a, *value):
        ele = self.find_name(name_a)
        if ele:
            ele.clear()
            ele.send_keys(*value)
            time.sleep(0.5)
        else: raise NoSuchElementException('%s Element Not Found' % name_a)

    def find_ids(self, id, ignore=False):
        try:
            return self.find_elements_by_id(id)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(id)

    def find_id(self, id, ignore=False):
        try:
            return self.find_element_by_id(id)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(id)

    def find_names(self, name_b, ignore=False):
        try:
            return self.find_elements_by_name(name_b)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(name_b)

    def find_name(self, name, ignore=False):
        try:
            return self.find_element_by_name(name)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(name)

    def csss(self, css, ignore=False):
        try:
            return self.find_elements_by_css_selector(css)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(css)

    def css(self, css, ignore=False):
        try:
            return self.find_element_by_css_selector(css)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(css)

    def xpaths(self, xpath, ignore=False):
        try:
            return self.find_elements_by_xpath(xpath)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(xpath)

    def xpath(self, xpath, ignore=False):
        try:
            return self.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(xpath)

    def xpath_local(self, xpath):
        eles = self.tree.xpath(xpath)
        if eles and len(eles) > 0:
            return eles[0]
        return None

    def xpaths_local(self, xpath):
        return self.tree.xpath(xpath)

    def fill_id(self, id, *value):
        ele = self.find_id(id)
        if ele:
            ele.clear()
            ele.send_keys(*value)
            time.sleep(0.5)
        else: raise NoSuchElementException('%s Element Not Found' % id)

    def wait_xpath(self, xpath):
        self.wait.until(lambda driver: driver.xpath(xpath))

    def down_until(self, xpath, stop=200, jump=20):
        _same_count = 0
        _count = 0
        while stop == -1 or (_count < stop):
            self.scroll_down()
            _c = len(self.xpaths(xpath))
            if _c == 0:
                break
            if _count ==_c:
                _same_count += 1
                time.sleep(1)
            else:
                _count = _c
                _same_count = 0

            if _same_count > jump:
                break
            time.sleep(1.5)

    def down_bottom(self):
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def click_xpaths(self, xpath, num=-1):
        _eles = []
        if isinstance(xpath, basestring):
            _eles = self.browser.xpaths(xpath)
        elif isinstance(xpath, list):
            for _x in xpath:
                _eles.extend(self.browser.xpaths(xpath))

        if len(_eles) > 0:
            if num != -1:
                start = random.randrange(3)
                end = start + random.randint(1, num)
                __eles = []
                for _e in range(start, end):
                    if len(_eles) < 1: break
                    __eles.append(_eles.pop(random.randrange(len(_eles))))
                _eles = __eles
            for _e in _eles:
                _e.click()
                time.sleep(random.randrange(1000, 5555, 50)/1000.0)

    def wait_xpath(self, xpath, timeout=None):
        if time is None: timeout = self.timeout
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))


    def highlight_xpath(self, xpath, ignore=True):
        ele = self.xpath(xpath, ignore)
        if ele:
            ele.send_keys(Keys.NULL)
            self.highlight(ele)

    def highlight_xpaths(self, xpath, ignore=True):
        eles = self.xpaths(xpath, ignore)
        for ele in eles:
            self.highlight(ele)

    def highlight(self, element):
        driver = element._parent
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, "background: yellow; border: 1px solid red;")
        element.send_keys(Keys.NULL)


    def hover(self, element):
        hov = ActionChains(self).move_to_element(element)
        hov.perform()
        time.sleep(1)

    def save_exe(self, exe_path):
        cPickle.dump({'command_executor': self.command_executor._url, 'session_id': self.session_id}, open(exe_path, 'wb'))

    def ele_xpath(self, element, xpath, ignore=False):
        try:
            return element.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(xpath)

class Browser(webdriver.Firefox, webdriver.Remote, BrowserMixin):

    def __init__(self, exe_path=None, firefox_profile=None, firefox_binary=None, string_proxy=None, timeout=180, capabilities=None, proxy=None, profile_preferences={}, **kwargs):
        self.timeout = timeout + 2
        self.wait_timeout = kwargs.get('wait_timeout', self.timeout)
        self.script_timeout = kwargs.get('script_timeout', self.timeout)

        if exe_path is not None and os.path.exists(exe_path):
            try:
                e = cPickle.load(open(exe_path, 'rb'))
                webdriver.Remote.__init__(self, command_executor=e['command_executor'], desired_capabilities={})
                self.session_id = e['session_id']
            except urllib2.URLError:
                self._init_instance(firefox_profile=firefox_profile, firefox_binary=firefox_binary, string_proxy=string_proxy, timeout=timeout, capabilities=capabilities, proxy=proxy, profile_preferences=profile_preferences, **kwargs)
        else:

            self._init_instance(firefox_profile=firefox_profile, firefox_binary=firefox_binary, string_proxy=string_proxy, timeout=timeout, capabilities=capabilities, proxy=proxy, profile_preferences=profile_preferences, **kwargs)

        self.wait = WebDriverWait(self, self.timeout)

        if exe_path is not None:
            self.save_exe(exe_path)

        self._html = ''

    def _init_instance(self, firefox_profile=None, firefox_binary=None, string_proxy=None, timeout=180, capabilities=None, proxy=None, profile_preferences={}, **kwargs):
        if firefox_profile is None:
            firefox_profile = LFirefoxProfile(profile_directory=kwargs.get('profile_directory', None), is_temp=kwargs.get('is_temp', False))

        firefox_profile.set_preference('browser.cache.disk.capacity', 131072)
        firefox_profile.set_preference('browser.cache.disk.smart_size.enabled', False)
        firefox_profile.set_preference('extensions.killspinners.timeout', self.timeout - 2)
        firefox_profile.set_preference('extensions.killspinners.disablenotify', True)
        firefox_profile.set_preference('extensions.firebug.showFirstRunPage', False)
        firefox_profile.set_preference('datareporting.healthreport.uploadEnabled', False)
        firefox_profile.set_preference('datareporting.healthreport.service.firstRun', False)

        firefox_profile.set_preference('network.proxy.type', 0)
        if string_proxy:
            proxyinfo = urlparse.urlparse(string_proxy)
            if proxyinfo.scheme == 'socks5':
                firefox_profile.set_preference('network.proxy.type', 1)
                firefox_profile.set_preference('network.proxy.socks', proxyinfo.hostname)
                firefox_profile.set_preference('network.proxy.socks_port', proxyinfo.port)
                firefox_profile.set_preference('network.proxy.socks_remote_dns', True)

        if kwargs.get('random_ua', False):
            user_agent = read_random_lines(USER_AGENT_DIR, 5)[0]
            firefox_profile.set_preference('general.useragent.override', user_agent)


        for k, v in profile_preferences.items():
            firefox_profile.set_preference(k, v)

        if sys.platform == 'win32':
            executable_path = os.path.join(GECKODRIVER, 'geckodriver_x64.exe')
        else:
            executable_path = os.path.join(GECKODRIVER, 'geckodriver_x64')
        webdriver.Firefox.__init__(self, firefox_profile=firefox_profile, firefox_binary=firefox_binary, timeout=timeout, capabilities=capabilities, proxy=None) # , executable_path=executable_path

        self.set_page_load_timeout(self.timeout)
        self.implicitly_wait(self.wait_timeout)
        self.set_script_timeout(self.script_timeout)



class BrowserRemote(webdriver.Remote, BrowserMixin):

    def __init__(self, exe_path=None):
        e = cPickle.load(open(exe_path, 'rb'))
        webdriver.Remote.__init__(self, command_executor=e['command_executor'], desired_capabilities={})
        self.session_id = e['session_id']




class BrowserPhantomJS(webdriver.PhantomJS):

    def __init__(self, executable_path="phantomjs",
                 port=0, desired_capabilities=DesiredCapabilities.PHANTOMJS,
                 service_args=[], service_log_path=None, string_proxy=None, timeout=180, **kwargs):

        self.timeout = timeout

        _desired_capabilities = {
            'phantomjs.page.settings.loadImages': False,
            'phantomjs.page.settings.resourceTimeout': '%s' % self.timeout * 1000,
            'phantomjs.page.settings.userAgent': kwargs.get('user_agent', read_random_lines(USER_AGENT_DIR, 5)[0]),

            'page.settings.loadImages': False,
            'page.settings.resourceTimeout': '%s' % self.timeout * 1000,
            'page.settings.userAgent': kwargs.get('user_agent', read_random_lines(USER_AGENT_DIR, 5)[0])

        }


        desired_capabilities.update(_desired_capabilities)


        if string_proxy:
            proxyinfo = urlparse.urlparse(string_proxy)
            if proxyinfo.scheme == 'socks5':
                service_args=[
                    '--proxy=%s:%s' % (proxyinfo.hostname, proxyinfo.port),
                    '--proxy-type=socks5',
                    ]

        super(BrowserPhantomJS, self).__init__(executable_path=executable_path,
            port=0, desired_capabilities=desired_capabilities,
            service_args=service_args, service_log_path=None)


        self.wait_timeout = kwargs.get('wait_timeout', self.timeout)
        self.script_timeout = kwargs.get('script_timeout', self.timeout)
        self.set_page_load_timeout(self.timeout)
        self.set_window_size(random.randint(800, 1500), random.randint(400, 800))



    def fill(self, name, *value):
        ele = self.find_name(name)
        if ele:
            ele.clear()
            ele.send_keys(*value)
            time.sleep(0.5)
        else: raise NoSuchElementException('%s Element Not Found' % name)

    def find_ids(self, id, ignore=False):
        try:
            return self.find_elements_by_id(id)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(id)

    def find_id(self, id, ignore=False):
        try:
            return self.find_element_by_id(id)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(id)

    def find_names(self, name, ignore=False):
        try:
            return self.find_elements_by_name(name)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(name)

    def find_name(self, name, ignore=False):
        try:
            return self.find_element_by_name(name)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(name)

    def csss(self, css, ignore=False):
        try:
            return self.find_elements_by_css_selector(css)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(css)

    def css(self, css, ignore=False):
        try:
            return self.find_element_by_css_selector(css)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(css)

    def xpaths(self, xpath, ignore=False):
        try:
            return self.find_elements_by_xpath(xpath)
        except NoSuchElementException as e:
            if ignore: return []
            else: raise NoSuchElementException(xpath)

    def xpath(self, xpath, ignore=False):
        try:
            return self.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            if ignore: return None
            else: raise NoSuchElementException(xpath)

    def fill_id(self, id, *value):
        ele = self.find_id(id)
        if ele:
            ele.clear()
            ele.send_keys(*value)
            time.sleep(0.5)
        else: raise NoSuchElementException('%s Element Not Found' % id)


if __name__ == '__main__':
    import time
    profile = LFirefoxProfile(profile_directory='K:\\xx\\fff', is_temp=False)
    browser = Browser(firefox_profile=profile, timeout=30)
    browser.implicitly_wait(5)
    browser.set_script_timeout(10)

    browser.get('http://www.baidu.com')

    e = browser.xpath('//div[@class="xxxxx"]')
    print e

    print 'ssssssssss'
    time.sleep(10)
    browser.quit()

