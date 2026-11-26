"""Contract tests on explicit toy inputs and supplied token sequences, never on generated verdicts."""
from dataclasses import replace
import math

import pytest

from tools.judge_contract import Arm, Item, Route, TextJudge, agreement, digest, summarize


class FixtureCodec:
    """One character per input token + BOS, so boundary lengths can be set exactly."""
    all_special_ids = [0]

    def encode(self, text, *, add_special_tokens, truncation):
        if not add_special_tokens or truncation:
            raise ValueError('fixture requires exact input with BOS')
        return [0, *map(ord, text)]

    def decode(self, ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        return ''.join({1:' Yes\n', 2:' NO ', 3:'Yesterday', 4:'No.', 0:'yes'}[i] for i in ids)


REV = digest(b'local toy revision')
ARM = Arm('local-fixture', 'parent', REV, 'primary')


def item(i=0):
    key = f'id-{i}'
    return Item(ARM, key, 'Which color?', 'Lemon yellow.', Route(key, REV, 'toy-text/v1', 'standard'))


def judge(role='judge', capacity=4096):
    return TextJudge(role, FixtureCodec(), capacity)


def observe(j, it, suffix):
    p = j.prepare(it)
    return j.parse_supplied(p, None if suffix is None else p.input_ids + tuple(suffix))


@pytest.mark.parametrize('role,header', [('judge', 'Behavior:'), ('judge_alt', '[BEHAVIOR]:')])
def test_selects_exact_role_and_substitutes_literal_data(role, header):
    j = judge(role)
    it = replace(item(), behavior='Keep {generation} verbatim.')
    p = j.prepare(it)
    text = ''.join(map(chr, p.input_ids[1:]))
    assert header+'\n'+it.behavior in text
    assert text.count(it.response) == 1 and text.endswith('Answer: [/INST]')
    if role == 'judge': assert 'do not count. \n' in text
    assert ('<<SYS>>' in text) == (role == 'judge')
    ctx = replace(it, route=replace(it.route, kind='contextual',context='The basket is empty.'),
                  target_context='The basket is empty.')
    pc = j.prepare(ctx)
    rendered = ''.join(map(chr, pc.input_ids[1:]))
    assert pc.template == 'prompt_contextual' and pc.template_sha256 != p.template_sha256
    assert rendered.count(ctx.target_context) == 1 and rendered.index(ctx.target_context) < rendered.index(it.behavior)
    for unresolved in [replace(ctx,target_context=None),replace(ctx,target_context='Other'),
                       replace(it,route=None),replace(it,route=replace(it.route,item_id='other')),
                       replace(it,route=replace(it.route,source_revision='main'))]:
        assert j.prepare(unresolved).reason == 'unscorable_context'


def test_length_limit_preserves_full_prompt_and_reserves_one_position():
    j = judge(capacity=2049)
    it = replace(item(), response='')
    n = 2048-j.prepare(it).input_length
    at_limit = replace(it,response='x'*n)
    p = j.prepare(at_limit)
    assert p.input_length == len(p.input_ids) == 2048 and p.reason is None
    for blocked in [judge(capacity=2048).prepare(at_limit), j.prepare(replace(at_limit,response='x'*(n+1)))]:
        assert blocked.reason=='unscorable_length' and not blocked.input_ids
        with pytest.raises(ValueError): j.parse_supplied(blocked,[1])


@pytest.mark.parametrize('suffix,label', [([1],'yes'),([2],'no'),([3],'invalid'),([4],'invalid'),
                                          ([0],'invalid'),([],'invalid'),([1,2],'invalid'),(None,'unscorable')])
def test_only_one_new_nonspecial_exact_label_is_valid(suffix,label):
    o=observe(judge(),item(),suffix)
    assert o.label==label and o.emitted==tuple(suffix or ())
    if label=='invalid': assert o.reason=='invalid_output' and o.decoded is not None
    if label=='unscorable': assert o.reason=='not_obtained'


def test_changed_prefix_or_wrong_judge_refused():
    j=judge(); p=j.prepare(item())
    with pytest.raises(ValueError): j.parse_supplied(p,[1])
    with pytest.raises(ValueError): judge('judge_alt').parse_supplied(p,p.input_ids+(1,))


def test_fixed_denominator_and_wilson_are_separate():
    j=judge(); plan=[item(i) for i in range(10)]; plan[-1]=replace(plan[-1],response=None)
    rows=[observe(j,it,suffix) for it,suffix in zip(plan,[[1]]*3+[[2]]*5+[[4],None],strict=True)]
    result=summarize(plan,rows,'judge')
    assert result['positive_fraction_bounds']==[.3,.5] and result['coverage']==.8
    assert result['counts']=={'yes':3,'no':5,'invalid':1,'unscorable':1}
    assert result['reasons']=={'invalid_output':1,'not_obtained':1}
    assert result['positive_rate'] is result['naive_wilson95'] is None
    full=summarize(plan[:8],rows[:8],'judge'); assert full['positive_rate']==3/8
    assert full['naive_wilson95']==pytest.approx([.1368443,.6942576],abs=1e-6)
    invalid=summarize(plan[8:9],rows[8:9],'judge'); assert invalid['valid_only_positive'] is None
    for invalid_plan, invalid_rows in [(plan,rows[:-1]),(plan,rows+[rows[0]]),(plan+[plan[0]],rows),([],[])]:
        with pytest.raises(ValueError): summarize(invalid_plan,invalid_rows,'judge')


def test_agreement_only_on_identical_valid_pairs():
    plan=[item(i) for i in range(5)]; a,b=judge(),judge('judge_alt')
    left=[observe(a,x,y) for x,y in zip(plan,[[1],[1],[2],[4],None])]
    right=[observe(b,x,y) for x,y in zip(plan,[[1],[2],[2],[1],[3]])]
    result=agreement(plan,left,right[::-1]); assert result['binary_table']==[[1,1],[0,1]]
    assert result['paired_valid_coverage']==3/5 and result['raw_agreement']==2/3
    assert math.isclose(result['kappa'],.4) and result['cross_tab']['unscorable']['invalid']==1
    assert agreement(plan[:1],left[:1],right[:1])['undefined_reason']=='zero_kappa_denominator'
    assert agreement(plan[-1:],left[-1:],right[-1:])['undefined_reason']=='no_valid_pairs'
    for other in [replace(plan[0],response='Blue.'),replace(plan[0],behavior='Which size?'),
                  replace(plan[0],arm=replace(ARM,stage='candidate'))]:
        with pytest.raises(ValueError): agreement(plan,left,[observe(b,other,[1]),*right[1:]])
    with pytest.raises(ValueError): replace(plan[0],arm=replace(ARM,name='over_refusal'))
