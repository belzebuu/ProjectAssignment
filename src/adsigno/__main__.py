#! /usr/bin/python

import adsigno.solve as solve
import adsigno.cml_parser as cml_parser


if __name__ == "__main__":
    options, dirname = cml_parser.cml_parse()
    solve.solve(dirname, options)
