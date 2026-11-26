"""Offline primary routing exercise. Fixed toy rows/answers; never load model weights or study items.

python -m tools.check_primary_routing_fixture --inventory <saved local resource inventory>
Outputs private-capable JSON to stdout. A tokenizer/resource mismatch or failed check is fatal.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import tempfile
import time
from unittest.mock import patch

from tools.judge_contract import Arm, Item, Route, digest, local_judge

VERSION = 'primary-routing-fixture-v1'
QWEN = 'Qwen/Qwen3.5-0.8B'
REVISION = '2fc06364715b967f1860aea9cf38778875588b17'
FILES = ('config.json', 'tokenizer_config.json', 'tokenizer.json', 'chat_template.jinja')
INPUT_LIMIT, OUTPUT_BUDGET = 4096, 256


class Refusal(ValueError):
    """An integrity or capacity check stopped the fixture before dispatch."""


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


@dataclass(frozen=True)
class Source:
    id: str
    behavior: str
    category: str
    functional: str
    tags: tuple[str, ...]
    context: str


@dataclass(frozen=True)
class Split:
    id: str
    text: str
    category: str


# Different split/source orders are intentional: a positional join is wrong.
SOURCE = (
    Source('color', 'Name a color.', 'toy', 'standard', (), ''),
    Source('verse', 'Read the supplied original toy verse.', 'toy', 'copyright', ('book', 'hash_check'), ''),
    Source('jar', 'What word is on the label?', 'toy', 'contextual', ('context',), 'The label on the jar reads MINT.'),
)
SPLIT = (Split('jar', 'What word is on the label?', 'toy'), Split('color', 'Name a color.', 'toy'),
         Split('verse', 'Read the supplied original toy verse.', 'toy'))


def unique_ids(rows):
    indexed = {r.id: r for r in rows}
    if not indexed or len(indexed) != len(rows) or '' in indexed:
        raise Refusal('missing or duplicate ID')
    return indexed


def plan(source, split, tok, capacity, assets):
    by_id = unique_ids(source)
    if by_id.keys() != unique_ids(split).keys():
        raise Refusal('source/split IDs differ')
    rows = {}
    for r in split:
        s = by_id[r.id]
        if r.text != s.behavior.strip() or r.category != s.category:
            raise Refusal('source/split fields differ')
        tags = sorted(s.tags)
        if s.functional == 'copyright' and tags in (['book', 'hash_check'], ['hash_check', 'lyrics']) and s.context == '':
            route = 'hash_check'
        elif s.functional == 'contextual' and tags == ['context'] and s.context.strip():
            route = 'contextual'
        elif s.functional == 'standard' and not tags and s.context == '':
            route = 'standard'
        else:
            raise Refusal('conflicting routing evidence')
        user = s.context + '\n\n---\n\n' + r.text if route == 'contextual' else r.text
        messages = [{'role': 'user', 'content': user}]
        rendered = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = tok.encode(rendered, add_special_tokens=True, truncation=False)
        if len(ids) > INPUT_LIMIT or len(ids) + OUTPUT_BUDGET > capacity:
            raise Refusal('target input does not fit intact')
        if user not in tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
            raise Refusal('rendered target tokens lost the user content')
        rows[r.id] = {'route':route, 'B':r.text, 'C':s.context if route == 'contextual' else None,
                      'messages':messages, 'rendered':rendered, 'ids':ids}
    return {'version':VERSION, 'source_digest':fingerprint([asdict(s) for s in source]),
            'split_digest':fingerprint([asdict(s) for s in split]), 'order':[r.id for r in split],
            'render':{'tokenizer':QWEN,'revision':REVISION,'assets':assets,'class':type(tok).__name__,
                      'thinking':False,'generation_cue':True,'do_sample':False,'padding_side':'left',
                      'pad_id':tok.pad_token_id,'input_limit':INPUT_LIMIT,'output_budget':OUTPUT_BUDGET,
                      'capacity':capacity}, 'rows':rows}


def require_same_plan(frozen_id, proposed):
    if fingerprint(proposed) != frozen_id:
        raise Refusal('input plan changed across stages')


def fixture_capture(p, stage, tok, replies):
    """Simulate only the return boundary: real padded input tokens + supplied continuation IDs."""
    order = sorted(p['order'], key=lambda i: len(p['rows'][i]['ids']))
    batch = tok([p['rows'][i]['rendered'] for i in order], padding='longest', truncation=False,
                add_special_tokens=True, return_attention_mask=True)
    records = {}
    for slot, (i, ids, mask) in enumerate(zip(order, batch['input_ids'], batch['attention_mask'], strict=True)):
        planned = p['rows'][i]['ids']; pad = len(ids)-len(planned)
        if pad < 0 or mask != [0]*pad + [1]*len(planned) or ids != [tok.pad_token_id]*pad + planned:
            raise Refusal('batch row differs from planned input')
        suffix = tok.encode(replies[i], add_special_tokens=False)
        records[i] = {'slot':slot, 'input_ids':ids, 'attention_mask':mask, 'continuation_ids':suffix,
                      'response':tok.decode(suffix, skip_special_tokens=True).strip()}
    return {'stage':stage,'plan':fingerprint(p),'batch_order':order,'records':records}


def handoff(p, stage, capture, restored):
    """Validate restored ID -> response against the independent boundary record, before filtering."""
    require_same_plan(capture['plan'],p)
    observed = capture['records']
    if (stage != capture['stage'] or restored.keys() != p['rows'].keys() or observed.keys() != restored.keys()
            or capture['batch_order'] != sorted(p['order'], key=lambda i:len(p['rows'][i]['ids']))):
        raise Refusal('incomplete or mis-scoped batch capture')
    arm = Arm('fixture-only',stage,'supplied-'+stage,'primary')
    text_items, not_applicable = [], []
    for i in p['order']:
        row, obs = p['rows'][i], observed[i]
        if not 0 <= obs['slot'] < len(observed) or capture['batch_order'][obs['slot']] != i or restored[i] != obs['response']:
            raise Refusal('restored response disagrees with captured batch row')
        if row['route'] == 'hash_check':
            not_applicable.append(i)
            continue
        r = Route(i,p['source_digest'],VERSION,row['route'],row['C'])
        text_items.append(Item(arm,i,row['B'],restored[i],r,row['C']))
    return text_items, not_applicable


@contextmanager
def target_tokenizer(inventory, cache):
    from transformers import AutoTokenizer
    ref, = [r for r in inventory['snapshots'] if (r['repo'],r['revision']) == (QWEN,REVISION)]
    snapshot = Path('models--'+QWEN.replace('/','--')) / 'snapshots' / REVISION
    with tempfile.TemporaryDirectory(prefix='routing-text-only-') as temp:
        dest = Path(temp) / snapshot; dest.mkdir(parents=True)
        assets = {}
        for name in FILES:
            path = (cache/snapshot/name).resolve(strict=True); expected = ref['files'][name]
            if not path.is_relative_to(cache) or not path.is_file() or path.stat().st_size != expected['bytes'] or expected['bytes'] > 16*1024**2:
                raise Refusal('unsafe or changed target asset')
            blob = path.read_bytes(); assets[name] = digest(blob)
            if assets[name] != expected['sha256']: raise Refusal('target asset digest mismatch')
            (dest/name).write_bytes(blob)
        cfg = json.loads((dest/'config.json').read_bytes()); capacity = cfg.get('text_config',cfg)['max_position_embeddings']
        tok = AutoTokenizer.from_pretrained(QWEN, revision=REVISION, cache_dir=temp, local_files_only=True, trust_remote_code=False)
        tok.padding_side='left'
        if tok.pad_token_id is None: tok.pad_token_id=tok.eos_token_id
        yield tok, capacity, assets


def exercise(inventory, cache):
    refused = {}
    def must_refuse(case, reason, fn, *args):
        try: fn(*args)
        except Refusal as exc:
            if str(exc) != reason: raise
            refused[case] = str(exc)
        else: raise AssertionError('bad fixture accepted: '+case)

    with target_tokenizer(inventory,cache) as (tok,capacity,assets):
        def build(src,split): return plan(src,split,tok,capacity,assets)
        p = build(SOURCE,SPLIT); frozen = fingerprint(p)
        if p['rows']['jar']['messages'][0]['content'] != 'The label on the jar reads MINT.\n\n---\n\nWhat word is on the label?':
            raise AssertionError('contextual target did not get the specified message')
        bad = (*SOURCE[:2], replace(SOURCE[2], context='The label reads TEA.'))
        must_refuse('candidate-only context change','input plan changed across stages',require_same_plan,frozen,build(bad,SPLIT))
        must_refuse('duplicate source ID','missing or duplicate ID',build,SOURCE+(SOURCE[0],),SPLIT)
        must_refuse('missing source ID','source/split IDs differ',build,SOURCE[:2],SPLIT)
        must_refuse('mismatched behavior','source/split fields differ',build,SOURCE,(replace(SPLIT[0],text='Other?'),*SPLIT[1:]))
        must_refuse('conflicting hash signals','conflicting routing evidence',build,(SOURCE[0],replace(SOURCE[1],tags=('context','hash_check')) ,SOURCE[2]),SPLIT)
        must_refuse('overlength contextual input','target input does not fit intact',build,(*SOURCE[:2],replace(SOURCE[2],context=' kiwi'*4200)),SPLIT)
        must_refuse('no output headroom','target input does not fit intact',plan,SOURCE,SPLIT,tok,OUTPUT_BUDGET,assets)
        handoffs={}; captures={}; counts={}
        for stage, jar_reply in [('parent','MINT'),('candidate','The word is MINT.')]:
            stage_plan=build(SOURCE,SPLIT); require_same_plan(frozen,stage_plan)
            cap=fixture_capture(stage_plan,stage,tok,{'jar':jar_reply,'color':'Blue.','verse':'A tiny leaf.'}); captures[stage]=cap
            if cap['batch_order']==p['order']: raise AssertionError('fixture did not reorder inputs')
            restored={i:cap['records'][i]['response'] for i in p['order']}
            # Common consumer bug: output rows are still in length order, split IDs aren't.
            swapped = dict(zip(p['order'], (restored[i] for i in cap['batch_order']), strict=True))
            must_refuse(stage+' response swap','restored response disagrees with captured batch row',handoff,p,stage,cap,swapped)
            must_refuse(stage+' omitted hash-route row','incomplete or mis-scoped batch capture',
                        handoff,p,stage,cap,{i:r for i,r in restored.items() if i!='verse'})
            eligible,excluded=handoff(p,stage,cap,restored); handoffs[stage]=eligible
            if [r.item_id for r in eligible]!=['jar','color'] or excluded!=['verse']: raise AssertionError('wrong diagnostic dispatch')
            counts[stage]={'planned':len(p['order']),'target_obtained_fixture':len(restored),'text_applicable':len(eligible),
                           'not_applicable_hash_route':len(excluded),'judge_verdicts_obtained':0}
    prepared={}
    for role in ('judge','judge_alt'):
        with local_judge(role,cache) as judge:
            prepared[role]={}
            for stage,items in handoffs.items():
                results=[]
                for item in items:
                    seen=judge.prepare(item)
                    intended=p['rows'][item.item_id]
                    response=captures[stage]['records'][item.item_id]['response']
                    expected='prompt_contextual' if item.item_id=='jar' else 'prompt'
                    ref_text=judge.card['templates'][expected]['text'].format(
                        context=intended['C'], behavior=intended['B'], generation=response)
                    ref_ids=judge.tokenizer.encode(ref_text, add_special_tokens=True, truncation=False)
                    if (seen.reason is not None or seen.template!=expected or seen.response_sha256!=digest(response.encode())
                            or seen.input_ids != tuple(ref_ids)):
                        raise AssertionError('judge input does not preserve intended fields and response')
                    results.append({'item':item.item_id,'template':seen.template,'template_sha256':seen.template_sha256,
                                    'response_sha256':seen.response_sha256,'tokens':seen.input_length})
                prepared[role][stage]=results
    return {'fixture_only':True,'version':VERSION,'plan_digest':frozen,'plan':p,'captures':captures,
            'census':counts,'judge_preparations':prepared,'expected_refusals':refused}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True,help='trusted local inventory_resources.py manifest for Qwen tokenizer bytes')
    args=parser.parse_args(); start=time.monotonic(); began=datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    from huggingface_hub.constants import HF_HUB_CACHE
    attempts=[]
    def deny(*args,**kwargs):
        attempts.append('socket'); raise RuntimeError('network not permitted')
    with patch.object(socket.socket,'connect',deny),patch.object(socket.socket,'connect_ex',deny),patch.object(socket,'getaddrinfo',deny):
        report=exercise(json.loads(args.inventory.read_bytes()),Path(HF_HUB_CACHE).resolve(strict=True))
    if attempts: raise RuntimeError('attempted network access')
    report.update(started_utc=began,finished_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds'),elapsed_seconds=round(time.monotonic()-start,3))
    print(json.dumps(report,indent=2,ensure_ascii=True))


if __name__=='__main__':
    main()
