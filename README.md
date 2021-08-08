# Purpose

This is a utility to help out when you've misplaced _a little bit_ of
your Algorand account mnemonic.

Algorand uses a 25 word, BIP39 account mnemonic.  This confuses some
users, since they may be used to 24 word mnemonics used by other
projects.  Never fear! The 25th word is a checksum word, it's derived
entirely from the first 24 words. If you fail to record it, this
utility will figure it out for you.

And it can do more. Suppose you wrote down 24 words, not because you
thought the 25th word was some sort of junk, but just because you
skipped one.  Then since you were used to 24 word projects, you didn't
notice that you had too few words.  Now, it's unclear which word is
missing, so the exact mnemonic can't be reconstructed. But it is
possible to figure out 25 different possibilities by assuming you
dropped the word from each possible spot, and reconstructing what
would need to be there to make the checksum work.  Now you can try
them all until you find the right one.

Trying 25 mnemonics is a pain in the butt!  If you recall the address
you're recovering, or even just the start of it, you can supply it as
`--address AF32...` If you do, then the candidate mnemonics will be
filtered to only those that start with the given prefix, which is
likely to winnow things down quickly.

But you don't remember the address! While not implemented yet, the
next trick is to hit the actual blockchain to see if the address in
question has any Algos.  After all, you probbaly wouldn't be so
interested in recovery if you had nothing in the account.

# Usage

py-algorand-sdk is the only needed module.  Use a venv, or install it
globally as you see fit. Then try:

```
./recover-algo-word.py sugar police obvious access unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

There's nothing to recover there, since you've supplied a 25 word
mnemonic, and the checksum worls. The associated address is printed
along with the mnemonic.

## You're missing a word

Now, try again, specifying that you forgot to record the final word by
using an underscore in its place.

```
./recover-algo-word.py sugar police obvious access unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb _
```

This time 2048 options are considered - one for each possible bip39
word. Only one is the proper checksum, so the same final output is
obtained after a tiny delay.

Suppose you didn't know which word you skipped when you recorded you
mnemonic.  Let's try without "unit" from the original. But we don't
replace unit with _ because we are pretending we didn't know which
spot we forgot.

```
./recover-algo-word.py sugar police obvious access blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

Since you only gave 24 words and no indication of where the 25th
should go, 51,200 possibilities must be considered (2048 possibilitues
in each of 25 locations).  That still doesn't take long, but an
annoyance is that 20 valid mnemonics are found. Usually, I'd
expect closer to 25 in this situation, but there are some constraints
that make it impossible to find a mnemonic for each possible missing
spot. The address for each mnemonic is printed, and perhaps that will
jog your memory.  If you had recalled your mnemonic started with G,
you might have given `--address G` as an extra command line argument,
which would have narrowed the field to just two possibilities. You
could try to recover them in your wallet, or look them up in
AlgoExporer(https://algoexplorer.io/) to figure out which holds your
account.

## You have one word wrong

If you had tried to supply all 25 words, but one was wrong, the
checksum would (usually) fail.  When that happens, the script performs
25 wildcard searches, replacing each word with _ in turn.  In effect,
it assumes that one of your words was mistyped, and tries to find all
the possible mnemonics that would work with the rest, in the given
order.

Let's try our first example with `dolphin` as the fourth word.

```
./recover-algo-word.py sugar police obvious dolphin unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

Searching 51,200 candidates, about 30 mnemonics are found that meet the
checksum.  Now would be a good time to use `--address`.  Sometimes
you'll get lucky, and far fewer candidates pass the checksumming.

# Obscure uses

Those are the most likely cases, but you can do more.

## Underscore as a prefix wildcard

Using an _ in place of a word indicates that a full 2048 word search
in that position must be done.  If you just have sloppy handwriting
and know the word starts with certain letter(s), xy_ will limit the
search to bip39 words that begin with xy.

For example, if you only remember that you first two words started
with s and p:

```
./recover-algo-word.py s_ p_ obvious access unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

checks 33000 mnemonics and finds 16 possibilities. `--address` or
AlgoExporer could narrow things down further.  By the way, if you also
forgot the third word, and used o_, you'd be searching 1.8M choices
which is much slower, but doable.  Any more and you're going to be
waiting a while.

## Comma, to try multiple choices

If, on the other hand, you don't have a prefix, but somehow think you
know that a particular spot is one of a few words, you can separate
them with commas, and it will try each, along with whatever other
wildcarding you're doing.

```
./recover-algo-word.py s_ police,favorite obvious access unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

will try 500 combos - 250 from the `s_` doubled by trying `police` and
`favorite` as the second word.


The comma doesn't seem very useful on its own - why would you know
the word is one from a small list?  The intent is to notice when a
word that _isn't_ a bip39 word at all is supplied, and the utility
would internally pick several similar words as options.  Currently
though, if a non bip39 word is supplied, nothing can be done. Unless
the first four characters match a bip39 word. Then, since bip39 is
unique in the first four characters, we print a warning but assume the
typo is after character 4 and use the indicated bip39 word.


```
./recover-algo-word.py sugary police obvious access unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

works fine, substituting `sugar` for `sugary`.  Because of this, you
can stop typing all of your words at the fourth character. You'll get no
warnings, as we assume shortened words are intentional:

```
./recover-algo-word.py suga poli obvi acce unit blur situ brow home usef manu coff eras pipe depu pani make rada scra prin glid abst kind abso matr
```

## Tilde for fuzzy matching

If you wrote your mnemonic down, but now you doubt your ability to
read your own handwriting, maybe you can tell which words are
especially poorly written.  In that case, end them with ~ and they
will be expanded to a set of similar words from the bip39 list.

Swap `aces~` for `access` and you'll be fine.

```
./recover-algo-word.py stupor~ police obvious aces~ unit blur situate brown home useful manual coffee erase pipe deputy panic make radar scrap print glide abstract kind absorb matrix
```

In fact, if you had tried `aces`, it would be reported as a non bip39
word, and suggestions for replacement would have been shown.
