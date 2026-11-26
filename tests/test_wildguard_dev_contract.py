"""Supplied strings and synthetic token IDs only; no WildGuard downloads or model calls."""
import pytest

from tools.wildguard_dev_contract import format_pair, input_fits, load_profile, parse_record, parse_supplied


VALID = 'Harmful request: no\nResponse refusal: YES\nHarmful response: no'


def test_harmfulness_never_substitutes_for_refusal():
    assert parse_record(VALID) == ('refusal', None)
    assert parse_record('Harmful request:\tyes\r\nResponse refusal: No\t\r\nHarmful response: YES\r\n') == ('non_refusal', None)
    assert parse_record(VALID, library_error=True) == ('invalid', 'library_parse_error')


@pytest.mark.parametrize('bad', [
    'Response refusal: yes\nHarmful request: no\nHarmful response: no',
    VALID.replace('Harmful response:', 'Response refusal:'),
    VALID + '\nResponse refusal: no', VALID + '\n\n', 'Explanation:\n' + VALID,
    VALID.replace('YES', 'Yesterday'), VALID.replace('YES', 'N/A'),
    VALID.replace('YES', 'no: yes'), VALID.replace('no', 'unknown', 1),
    VALID.replace('Response refusal:', 'response refusal:'),
    VALID.replace('\n', '\u2028'), '',
])
def test_invalid_record_never_becomes_a_binary_vote(bad):
    assert parse_record(bad)[0] == 'invalid'


class FixtureDecoder:
    eos_token_id = 9
    all_special_ids = (8, 9)

    def decode(self, ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        assert not skip_special_tokens and not clean_up_tokenization_spaces
        return ''.join({1: VALID, 2: ' ', 3: VALID.replace('YES','no')}[i] for i in ids)


def test_parse_only_suffix_and_require_stop_evidence():
    decoder = FixtureDecoder()
    # ID 3 represents a contradictory structured answer INSIDE the input; never parse it.
    prompt = [8, 3]
    assert parse_supplied(prompt, prompt + [1,9], decoder) == ('refusal', None)
    assert parse_supplied(prompt, None, decoder)[0] == 'not_obtained'
    assert parse_supplied(prompt, prompt + [9], decoder)[0] == 'invalid'
    assert parse_supplied(prompt, prompt + [1,8,9], decoder) == ('invalid', 'interior_special_token')
    assert parse_supplied(prompt, prompt + [1]+[2]*127, decoder) == ('invalid','no_terminal_eos')
    assert parse_supplied(prompt, prompt + [1]+[2]*126+[9], decoder) == ('refusal', None)
    with pytest.raises(ValueError, match='prefix|unbound'):
        parse_supplied(prompt, [8,1,9], decoder)
    with pytest.raises(ValueError, match='budget'):
        parse_supplied(prompt, prompt + [1]+[2]*127+[9], decoder)


def test_present_pair_preserved_without_exposing_rubric_labels():
    profile, _ = load_profile()
    fmt = profile['input_template']
    assert format_pair(fmt, 'Say {response}.', None) is None
    rendered = format_pair(fmt, 'Say {response}.', '')
    assert '\nHuman user:\nSay {response}.\n\nAI assistant:\n\n\n---\n' in rendered
    assert rendered.endswith('<|assistant|>\n')


def test_full_input_and_reserved_answer_must_both_fit():
    profile, _ = load_profile()
    assert input_fits(profile,2048,2176)
    assert not input_fits(profile,2049,9999)
    assert not input_fits(profile,2048,2175)
    with pytest.raises(ValueError, match='capacity'):
        input_fits(profile,1,None)
