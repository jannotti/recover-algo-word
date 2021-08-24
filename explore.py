#!/usr/bin/env python

import sys

import json
from urllib.request import urlopen, Request


url = "https://algoexplorerapi.io/v1/account/"
headers = {"accept": "application/json", "user-agent": "please"}


def algos(addr):
    with urlopen(Request(url + addr,  headers=headers)) as resp:
        j = json.loads(resp.read().decode("utf-8"))
        return j["amount"]


def active(addr):
    return algos(addr) > 0


if __name__ == "__main__":
    for addr in sys.argv[1:]:
        print(active(addr))
