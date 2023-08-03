#! /usr/bin/python

from adsigno import solve
from adsigno import cml_parser


if __name__ == "__main__":
    options = cml_parser.cml_parse()
    solve(options)
