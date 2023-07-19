import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, Tuple
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.port import Port
from pinaht.modules.module import Module
from pinaht.knowledge.types.fstree import File
from pinaht.knowledge.types.webserverfstree import WebserverFsTree
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.service import Service


WORDLIST = ["test", "hidden", "secret", "geheim"]


class WebserverFilesModule(Module):
    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        webserver_precondition = check_type(Service)
        port_precondition = check_type(Port)

        return {
            "meta": (
                {
                    "target": target_precondition,
                    "ip_address": ip_address_precondition,
                    "webserver": webserver_precondition,
                    # TODO: maybe check for specific webserver (e.g. Apache, Nginx)
                    "port": port_precondition,
                },
                merge([is_parent("target", ["ip_address", "webserver"]), is_parent("webserver", ["port"])]),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        target = keyed_knowledge["target"]
        ip_address = str(keyed_knowledge["ip_address"])
        port = keyed_knowledge["port"]

        urls = list(crawl(f"http://{ip_address}:{port}"))

        # insert beginning from root
        urls.sort()
        filesystem = File("", "", "")
        for url in urls:
            parsed_url = urlparse(url)
            path = parsed_url.path.lstrip("/")
            if path:
                filesystem.insert(path, "", "", "")

        # add knowledge if any URLs were found
        if urls:
            parsed_url = urlparse(urls[0])
            host = f"{parsed_url.scheme}://{parsed_url.netloc}"
            fs_tree = WebserverFsTree(filesystem, host)
            buffered_module_manager.add_knowledge(target, "filesystem", fs_tree, 1.0)


def get_urls(target):
    urls = set()
    try:
        response = requests.get(target)
        if response.status_code == 200:
            # add target itself
            urls.add(response.url)

            # parse page HTML
            html = BeautifulSoup(response.text, "html.parser")

            # verify response contains valid HTML
            if html.find():
                tags = html.findAll("a")
                urls.update(map(lambda tag: tag.get("href"), tags))

                def clean_url(url):
                    # convert relative to absolute URL and discard parameters/fragments
                    absolute_url = urljoin(target if target.endswith("/") else f"{target}/", url)
                    parsed_url = urlparse(absolute_url)
                    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

                urls = set(map(clean_url, urls))
    except requests.exceptions.RequestException:
        # ignore invalid URLs
        pass
    return urls


def crawl(target):
    found_urls = set()

    # crawl URLs recursively, beginning with target
    urls = set({target})
    while urls:
        url = urls.pop()
        new_urls = get_urls(url)

        # check for secret URLs
        for word in WORDLIST:
            new_url = urljoin(url, word)
            new_urls.update(get_urls(new_url))

        # check suburls
        parsed_url = urlparse(url)
        split_path = parsed_url.path.split("/")
        if len(split_path) >= 3:
            for i in range(2, len(split_path)):
                suburl = f"{parsed_url.scheme}://{parsed_url.netloc}/{'/'.join(split_path[1:i])}"
                new_urls.add(suburl)

        def filter_url(url):
            # ignore other domains and already found URLs
            return urlparse(url).netloc == urlparse(target).netloc and url not in found_urls

        new_urls = set(filter(filter_url, new_urls))
        urls.update(new_urls)
        found_urls.update(new_urls)

    return found_urls
