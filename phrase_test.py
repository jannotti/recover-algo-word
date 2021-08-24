
import recover_algo_word as raw


def test_bip39_choices():
    assert raw.bip39_choices("stop") == []
