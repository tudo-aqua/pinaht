import logging
import _thread
import http.server
import socketserver
import os
from netifaces import interfaces, ifaddresses, AF_INET


class FileManager:
    """
    The FileManager class manages file requests from modules. The files are located in pinaht\assets.
    """

    def __init__(self, netmask):
        """
        constructor for FileManager
        """
        self.PATH_TO_ASSETS = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../assets")
        self.port = 1337
        self.netmask = netmask

        class HTTPHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                asset_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../assets"))
                fullpath = os.path.join(asset_path, path[1:])
                return fullpath

        self.HANDLER = HTTPHandler
        self._logger = logging.getLogger("FileManager")

    def get_file(self, module_name, file_name):
        """
        gets the requested file
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :returns: the requested File
        """
        path = os.path.join(self.PATH_TO_ASSETS, module_name, file_name)
        file = open(path, "r")

        return file

    def get_file_path(self, module_name, file_name, sanitized=False):
        """
        creates path to the requested file
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :param sanitized: embed path in quotation marks if it contains spaces
        :returns: path to the requested file
        """
        path = os.path.join(self.PATH_TO_ASSETS, self.get_local_file_path(module_name, file_name))
        if " " in path and sanitized:
            path = "'" + path + "'"
        return path

    def get_local_file_path(self, module_name, file_name, sanitized=False):
        """
        creates path to the requested file (local with respect to assets)
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :param sanitized: embed path in quotation marks if it contains spaces
        :returns: path to the requested file
        """
        path = os.path.join(module_name, file_name)
        if " " in path and sanitized:
            path = "'" + path + "'"
        return path

    def start_server(self):
        """
        starts the FileServer
        """
        _thread.start_new_thread(self.__server_function, ())

    def __server_function(self):
        while True:
            try:
                self.httpd = socketserver.TCPServer(("", self.port), self.HANDLER)
                self._logger.info("Started fileserver at port " + str(self.port))
                break
            except OSError:
                self._logger.warning("Could not start server at port " + str(self.port) + ", trying again.")
                self.port += 1
        self.httpd.serve_forever()

    def shutdown_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def get_local_ips(self):
        """
        iterates over all interfaces and returns all ip addresses bind by them
        :returns: all IP addresses held by the executing server
        """
        addr = []
        for iface_name in interfaces():
            addresses = [i["addr"] for i in ifaddresses(iface_name).setdefault(AF_INET, [{"addr": "No IP addr"}])]
            addr.append(addresses.pop())

        addresses = [a for a in addr if a != "No IP addr"]

        return addresses

    def get_file_url_all(self, module_name, file_name):
        """
        creates path to the requested file
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :returns: all possible urls to the requested file
        """
        addresses = self.get_local_ips()

        urls = [
            (a, "http://" + a + ":" + str(self.port) + "/" + self.get_local_file_path(module_name, file_name))
            for a in addresses
        ]

        return urls

    def get_file_url_not_local(self, module_name, file_name):
        """
        creates path to the requested file
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :returns: first possible url to the requested file which is not 127.0.0.1
        """
        urls = self.get_file_url_all(module_name, file_name)
        urls = [u for (ip, u) in urls if ip != "127.0.0.1"]

        return urls

    def get_file_url_reachable_from_ip(self, module_name, file_name, ip):
        """
        creates path to the requested file
        :param module_name: the name of the module which has requested the file
        :param file_name: the name of the requested file
        :param ip: the ip from which it should be reachable
        :returns: first possible url to the requested file which is not 127.0.0.1
        """
        urls = self.get_file_url_not_local(module_name, file_name)
        # TODO ultra hacky
        ip_str_list = str(ip).split(".")
        new_ip = ".".join(ip_str_list[:3])
        urls = [u for u in urls if u.find(new_ip) == 7]

        return urls[0]
