from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.version import Version
import logging


def test():
    logger = logging.getLogger("service test")
    service = Service(None, 80, "Microsoft", "VS Code", Version("10.2"))
    logger.debug(str(service))
    logger.debug(service == service)
