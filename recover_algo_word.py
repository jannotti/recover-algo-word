#!/usr/bin/env python
import argparse
import difflib
import math
import sys

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


reported = {}


def bip39_choices(pattern):
    if pattern in mnemonic.word_to_index:
        return [pattern]
    comma = pattern.find(',')
    if comma >= 0:
        return bip39_choices(pattern[:comma])+bip39_choices(pattern[comma+1:])

    underscore = pattern.find('_')
    if underscore >= 0:
        if underscore > 3:
            print(f"Useless _ in '{pattern}' " +
                  "bip39 words are unique in the first four characters.")
        prefix = pattern[:underscore]
        return [w for w in bip39 if w.startswith(prefix)]

    if pattern.endswith("~"):
        return difflib.get_close_matches(pattern[:-1], bip39, 6, .6)

    if pattern not in reported:
        print(f"{pattern} is not a bip39 word.")

    if len(pattern) > 4 and pattern[:4] in mnemonic.word_to_index:
        word = mnemonic.index_to_word[mnemonic.word_to_index[pattern[:4]]]
        if pattern not in reported:
            print(f"Using {word} for {pattern}.")
        reported[pattern] = 1
        return [word]

    matches = difflib.get_close_matches(pattern, bip39, 6, .6)
    if matches:
        print(f"Consider '{','.join(matches)}' or equivalently '{pattern}~'.")

    return []


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


def has_algos(addr):
    import explore
    explore.active(addr)


found = []


def print_candidate(candidate, prefix):
    phrase = " ".join([mnemonic.index_to_word[mnemonic.word_to_index[c]]
                       for c in candidate])
    sk = mnemonic.to_private_key(phrase)
    address = account.address_from_private_key(sk)
    if address.startswith(prefix):
        if args.explore and not has_algos(address):
            return
        print(address, phrase)
        found.append([address, phrase])


def check_choices(choices):
    found = 0
    for c in candidates(choices):
        if chk25(c):
            found += 1
            print_candidate(c, args.address.upper())
    return found


def count_choices(choices):
    return math.prod([len(c) for c in choices])


def index_pairs(top):
    for lo in range(top-1):
        for hi in range(lo+1, top):
            yield (lo, hi)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Recover Algorand mnemonics when some is missing or wrong.')
    parser.add_argument('words', metavar='N', nargs='+',
                        help='sequence of of words in account mnemonic')
    parser.add_argument('--address', default='',
                        help='the account being recovered (prefix), if known')
    parser.add_argument('--explore', action='store_true',
                        help='use algoexplorer API to filter inactive accounts')

    args = parser.parse_args()
    words = [w.lower() for w in args.words]

    choices = [bip39_choices(w.lower()) for w in words]
    count = count_choices(choices)

    if len(words) == 25:
        if count == 1:          # 25 words given, no wildcarding
            if check_choices(choices) == 0:
                print("Bad checksum. Finding similar mnemonics")
                print(f" Trying swaps of all pairs. {25*24} possibilities")
                # Maybe this should be a switch that affects all
                # check_choices calls.  That would change all our
                # reporting about possibility count, but it would be
                # cool to always handle swaps.
                for lo, hi in index_pairs(25):
                    choices[hi], choices[lo] = choices[lo], choices[hi]
                    check_choices(choices)
                    choices[hi], choices[lo] = choices[lo], choices[hi]
                if len(found) > 0:  # Add a switch to keep going?
                    sys.exit(0)
                print(f" Trying to replace each word. {25*2048} possibilities")
                for i in range(25):
                    wild = choices[:i] + [bip39] + choices[i+1:]
                    check_choices(wild)
        elif count > 1:
            print(f"Trying {count} possibilities")
            check_choices(choices)

    if len(words) == 24:        # Missing one word. Insert _ in each slot
        if count > 0:
            print(f"Trying {25*2048*count} possibilities")
            for i in range(25):
                wild = choices[:i] + [bip39] + choices[i:]
                check_choices(wild)

    if len(words) == 23:
        # This is at least 600 * 4M = 2.5B possibilities (more if any
        # words have wildcards).  Utterly hopeless without an
        # --address to winnow them down, and will take days anyway.
        if count > 0:
            print(f"Trying {24*25*2048*2048*count} possibilities")
            for lo, hi in index_pairs(25):
                wild = choices[:lo] + [bip39] + choices[lo:hi] + [bip39] + choices[hi:]
                check_choices(wild)

    if 1 < len(words) <= 22:
        print("No. I can't work miracles. " +
              "Finding >= 3 words is only possible if _ indicates their positions.")

    if len(words) == 1:
        # Useful for debugging a pattern
        print(str(choices[0]))
    elif count == 0:
        print("Unable to find candidates to check.")

    if len(found) > 1 and not args.address:
        print("Multiple possibilities. Narrow possibilities with --address")
