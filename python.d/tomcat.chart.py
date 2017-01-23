# -*- coding: utf-8 -*-
# Description: tomcat netdata python.d module
# Author: Pawel Krupa (paulfantom)

from base import UrlService
from re import compile

# default module values (can be overridden per job in `config`)
# update_every = 2
priority = 60000
retries = 60

# charts order (can be overridden if you want less charts, or different order)
ORDER = ['accesses', 'volume', 'threads', 'jvm']

CHARTS = {
    'accesses': {
        'options': [None, "Requests", "requests/s", "statistics", "tomcat.accesses", "area"],
        'lines': [
            ["requestCount", 'accesses', 'incremental']
        ]},
    'volume': {
        'options': [None, "Volume", "KB/s", "volume", "tomcat.volume", "area"],
        'lines': [
            ["bytesSent", 'volume', 'incremental', 1, 1024]
        ]},
    'threads': {
        'options': [None, "Threads", "current threads", "statistics", "tomcat.threads", "line"],
        'lines': [
            ["currentThreadCount", 'current', "absolute"],
            ["currentThreadsBusy", 'busy', "absolute"]
        ]},
    'jvm': {
        'options': [None, "JVM Free Memory", "MB", "statistics", "tomcat.jvm", "area"],
        'lines': [
            ["free", None, "absolute", 1, 1048576]
        ]}
}

class Service(UrlService):
    def __init__(self, configuration=None, name=None):
        UrlService.__init__(self, configuration=configuration, name=name)
        self.url = self.configuration.get('url', "http://127.0.0.1:8080/manager/status?XML=true")
        self.order = ORDER
        self.definitions = CHARTS
        self.port = compile(r'(?:http://.*?:)(\d*)(?:/)').search(self.url).groups()[0]
        self.jvm_regex = compile(r'(?:jvm>)(.*?)(</jvm)')
        self.inner_regex = compile(r'([\w]+)=\\?[\'\"](\d+)\\?[\'\"]')
        self.outer_regex = compile(r'(?:name=\'"http-\w{3}-' + escape(self.port) + u'"\')(.*?)(?:<\/connector)')

    def check(self):
        if not self.url.endswith('manager/status?XML=true'):
            self.error('Bad url(%s). Must be http://<ip.address>:<port>/manager/status?XML=true' % self.url)
            return False

        return UrlService.check(self)

    def _get_data(self):
        """
        Format data received from http request
        :return: dict
        """
        data = self._get_raw_data()
        if data:
            jvm_data = self.jvm_regex.search(data).groups()[0]
            connection_data = self.outer_regex.search(data).groups()[0]
            relevant_data = jvm_data + connection_data
            data = dict(self.inner_regex.findall(relevant_data))
        return data or None
