#! /usr/bin/python

from adsigno import process
from adsigno import cml_parser
import logging


if __name__ == "__main__":
    options = cml_parser.cml_parse()
    process(options)
