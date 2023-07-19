import test.precondition_test as precondition_test
import logging
import sys  # noqa F841

sys.path.insert(0, "../pinaht")  # noqa F841


def main():
    # setup logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("__init__")
    logger.info("Starting")
    precondition_test.test()
