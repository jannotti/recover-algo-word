#!/usr/bin/env python
import argparse
import difflib
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
        prefix = pattern[0:underscore]
        return [w for w in bip39 if w.startswith(prefix)]

    if pattern.endswith("~"):
        return difflib.get_close_matches(pattern[:-1], bip39, 6, .6)

    if pattern not in reported:
        print(f"{pattern} is not a bip39 word.")

    if len(pattern) > 4 and pattern[0:4] in mnemonic.word_to_index:
        if pattern not in reported:
            print(f"Using {pattern[0:4]}.")
        reported[pattern] = 1
        return [pattern[0:4]]
    reported[pattern] = 1
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


found = []


def print_candidate(candidate, prefix):
    phrase = " ".join([mnemonic.index_to_word[mnemonic.word_to_index[c]]
                       for c in candidate])
    sk = mnemonic.to_private_key(phrase)
    address = account.address_from_private_key(sk)
    prefix = prefix.upper()
    if address.startswith(prefix):
        print(address, phrase)
        found.append([address, phrase])


def check_choices(choices):
    found = 0
    for c in candidates(choices):
        if chk25(c):
            found += 1
            print_candidate(c, args.address)
    return found


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Recover Algorand mnemonics when some details are missing (or wrong).')
    parser.add_argument('words', metavar='N', nargs='+',
                        help='sequence of of words in account mnemonic')
    parser.add_argument('--address', default="",
                        help='the account being recovered (prefix), if known')

    args = parser.parse_args()
    words = [w.lower() for w in args.words]

    if len(words) == 25:
        choices = [bip39_choices(w) for w in words]
        count = math.prod([len(c) for c in choices])
        if count == 1:          # 25 words given, no wildcarding
            if check_choices(choices) == 0:
                print(f"Bad checksum. Finding similar mnemonics among {25*2048}.")
                # Try replacing each word with _.
                for i in range(24):
                    wild = words[:i] + ["_"] + words[i+1:]
                    check_choices([bip39_choices(w) for w in wild])
        elif count > 1:
            print(f"Trying {count} possibilities")
            check_choices(choices)
        else:
            print("Unable to find candidates to check.")

    if len(words) == 24:        # Missing one word. Insert _ in each slot
        choices = [bip39_choices(w) for w in words]
        count = math.prod([len(c) for c in choices])
        if count > 0:
            print(f"Trying {25*2048*count} possibilities")
            for i in range(25):
                wild = words[:i] + ["_"] + words[i:]
                check_choices([bip39_choices(w) for w in wild])

    if len(words) < 24:
        print("I can't work miracles. " +
              "Finding two words is only possible, if _ indicates their positions.")

    if len(found) > 1 and not args.address:
        print("Multiple possibilities. Narrow possibilities with --address")
