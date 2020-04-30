from collections import namedtuple
from datetime import datetime
from os import environ
from typing import *
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, getLogger
import colorama
from termcolor import colored

colorama.init()


class LogLevelStyling(NamedTuple):
    base: list = ["white", []]
    emphasis: list = [None, ["bold"]]
    icon: Optional[str] = None


SUCCESS = 666

LOG_FORMAT_STYLES: Dict[int, Dict[str, Callable[[str], str]]] = {
    DEBUG: {
        "prepend": lambda o: "  ",
        "base": lambda o: colored(o, attrs=["dark"]),
        "emphasis": lambda o: colored(o, "cyan", attrs=["bold", "dark"]),
    },
    INFO: {
        "prepend": lambda o: colored("ℹ️", "cyan") + " ",
        "base": lambda o: o,
        "emphasis": lambda o: colored(o, "cyan"),
    },
    SUCCESS: {
        "prepend": lambda o: colored("✓", "green") + " ",
        "base": lambda o: colored(o, "green"),
        "emphasis": lambda o: colored(o, "white", attrs=["bold"]),
    },
    WARNING: {
        "prepend": lambda o: "  ",
        "base": lambda o: colored(o, "yellow"),
        "emphasis": lambda o: colored(o, "white", attrs=["bold"]),
    },
    ERROR: {
        "prepend": lambda o: "  ",
        "base": lambda o: colored(o, "red"),
        "emphasis": lambda o: colored(o, "white", attrs=["bold"]),
    },
    CRITICAL: {
        "prepend": lambda o: "  ",
        "base": lambda o: colored(o, "white", "on_red"),
        "emphasis": lambda o: colored(o, "white", "on_red", attrs=["bold"]),
    },
}

Colorizers = namedtuple("Colorizers", ["base", "emphasis", "prepend"])
logger = getLogger()


def get_log_formatter(
    levelno: int, verbatim: bool = False
) -> Callable[[str, List[Any]], str]:
    colorize = Colorizers(**LOG_FORMAT_STYLES[levelno])

    def formatter(text: str, *emphasized, **emphasized_kwargs) -> str:
        text = colorize.base(text)
        now = datetime.now().strftime("%H:%M:%S")
        if not verbatim:
            emphasized = [
                colorize.emphasis(el) + colorize.base("").replace("\033[0m", "")
                for el in emphasized
            ]
            emphasized_kwargs = {
                k: colorize.emphasis(v) + colorize.base("").replace("\033[0m", "")
                for k, v in emphasized_kwargs.items()
            }
            text = text.format(*emphasized, **emphasized_kwargs)
        return colored(now, attrs=["dark"]) + "  " + colorize.prepend(text) + text

    return formatter


def debug(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(DEBUG)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= DEBUG:
        print(text)
    # logger.debug(text)


def info(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(INFO)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= INFO:
        print(text)
    # logger.info(text)


def success(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(SUCCESS)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= INFO:
        print(text)
    # logger.info(text)


def warn(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(WARNING)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= WARNING:
        print(text)
    # logger.warn(text)


def error(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(ERROR)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= ERROR:
        print(text)
    # logger.error(text)


def critical(text: str, *emphasized, **emphasized_kwargs):
    text = get_log_formatter(CRITICAL)(text, *emphasized, **emphasized_kwargs)
    logger.setLevel(environ.get("log-level", "INFO"))
    if logger.getEffectiveLevel() <= CRITICAL:
        print(text)
    # logger.critical(text)


class verbatim:
    def debug(text: str):
        text = get_log_formatter(DEBUG, verbatim=True)(text)
        logger.setLevel(environ.get('log-level', 'DEBUG'))
        if logger.getEffectiveLevel() <= CRITICAL:
            print(text)
