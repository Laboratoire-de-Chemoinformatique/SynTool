"""Module containing classes for muting the redundant logging from complementary
packages and tools."""

import logging
import os
import sys


class GeneralException(Exception):
    """SynTool is multilayered software combining the code working with reaction data,
    machine learning, search algorithms, and interface modules.

    The complexity of SynTool code now doesn’t allow for the specification of all fail
    scenarios. This general exception is a placeholder and is supposed to be extended to
    properly cover all exceptions in SynTool.
    """



class DisableLogger:
    """This class mute redundant logging information.

    Adopted from
    https://stackoverflow.com/questions/2266646/how-to-disable-logging-on-the-standard-error-stream.
    """

    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exit_type, exit_value, exit_traceback):
        logging.disable(logging.NOTSET)


class HiddenPrints:
    """This class mute redundant printing information.

    Adopted from
    https://stackoverflow.com/questions/8391411/how-to-block-calls-to-print.
    """

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
