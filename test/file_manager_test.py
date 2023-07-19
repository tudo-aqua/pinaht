import logging
from pinaht.file_manager import FileManager


def get_file_test():
    logger = logging.getLogger("FileManagerTest")
    logger.debug("start FileManagerTest")
    testfile = open("../assets/example_module/example_file", "r")
    file_manager = FileManager()
    returned_file = FileManager.get_file(file_manager, "example_module", "example_file")
    logger.debug(testfile.read() == returned_file.read())
    logger.debug("end FileManagerTest")
