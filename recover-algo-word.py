#!/usr/bin/env python
import argparse
import math

from algosdk.wordlist import word_list_raw
import algosdk.mnemonic as mnemonic
import algosdk.account as account

known = """
sugar police obvious access unit blur
situate brown home useful manual coffee
erase pipe deputy panic make radar
scrap print glide abstract kind absorb
matrix
"""

bip39 = word_list_raw().split()


def bip39_choices(pattern):
    if pattern in mnemonic.word_to_index:
        return [pattern]
    comma = pattern.find(',')
    if comma >= 0:
        return bip39_choices(pattern[:comma])+bip39_choices(pattern[comma+1:])

    under = pattern.find('_')
    if under == -1:
        print(f"{pattern} is not a bip39 word.")
        if len(pattern) > 4 and pattern[0:4] in mnemonic.word_to_index:
            print(f"Using {pattern[0:4]}.")
            return [pattern[0:4]]
        return []
    if under > 3:
        print(f"Useless _ in '{pattern}' " +
              "bip39 words are unique in the first four characters.")
    prefix = pattern[0:under]
    return [w for w in bip39 if w.startswith(prefix)]


def chk25(words):
    check = mnemonic.word_to_index[words[-1]]
    m_indexes = [mnemonic.word_to_index[w] for w in words[:-1]]
    m_bytes = mnemonic._to_bytes(m_indexes)
    if not m_bytes[-1:] == b'\x00':
        return False
    return check == mnemonic._checksum(m_bytes[:32])


def candidates(options):
    if not options:
        yield []
        return

    head = options[0]
    for candidate in candidates(options[1:]):
        for h in head:
            yield [h, *candidate]


def print_candidate(candidate, prefix):
    phrase = " ".join([mnemonic.index_to_word[mnemonic.word_to_index[c]]
                       for c in candidate])
    sk = mnemonic.to_private_key(phrase)
    address = account.address_from_private_key(sk)
    prefix = prefix.upper()
    if address.startswith(prefix):
        print(address, phrase)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Recover Algorand mnemonics when missing some details.')
    parser.add_argument('words', metavar='N', nargs='+',
                        help='sequence of of words in account mnemonic')
    parser.add_argument('--address', default="",
                        help='the account being recovered (prefix), if known')

    args = parser.parse_args()
    words = [w.lower() for w in args.words]

    tried = 0

    if len(words) == 25:
        choices = [bip39_choices(w) for w in words]
        count = math.prod([len(c) for c in choices])
        print(f"Trying {count} possibilities")
        for c in candidates(choices):
            tried += 1
            if chk25(c):
                print_candidate(c, args.address)
            if tried % 100000 == 0:
                print(tried)

    if len(words) == 24:
        choices = [bip39_choices(w) for w in words]
        count = math.prod([len(c) for c in choices])
        print(f"Trying {25*2048*count} possibilities")
        for i in range(25):
            wild = words[:i] + ["_"] + words[i:]
            choices = [bip39_choices(w) for w in wild]
            for c in candidates(choices):
                tried += 1
                if chk25(c):
                    print_candidate(c, args.address)
                if tried % 100000 == 0:
                    print(tried)

    if len(words) < 24:
        print("I can't work miracles")
