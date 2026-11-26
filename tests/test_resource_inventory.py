"""Local resource fingerprints: partial snapshots are repeatable, not complete."""
import hashlib
import json

import pytest

from tools.inventory_resources import ENGLISH_TABLES, ROLES, inventory, main


@pytest.fixture
def inputs(tmp_path):
    rev = hashlib.sha1(b'fixture revision').hexdigest()
    cfg = tmp_path / 'harness.json'
    cfg.write_text(json.dumps({role: {'id': 'owner/test', 'revision': rev} for role in ROLES}))
    hub = tmp_path / 'hub'
    snapshot = hub / 'models--owner--test' / 'snapshots' / rev
    snapshot.mkdir(parents=True)
    for name in ('config.json', 'tokenizer_config.json', 'tokenizer.json'):
        (snapshot / name).write_bytes(b'{}')
    punkt = tmp_path / 'english'
    punkt.mkdir()
    for name in ENGLISH_TABLES:
        (punkt / name).write_bytes(b'local table')
    return cfg, hub, snapshot, punkt


def test_sharded_model_coverage_and_deduplicated_roles(inputs):
    cfg, hub, model, punkt = inputs
    (model / 'model.safetensors.index.json').write_text(json.dumps({'weight_map': {'a': 'part1', 'b': 'part2'}}))
    (model / 'part1').write_bytes(b'first')
    [partial] = inventory(cfg, hub, punkt)['snapshots']
    assert partial['roles'] == list(ROLES)
    assert 'model.safetensors.index.json: part2' in partial['missing_standard_inputs']
    (model / 'part2').write_bytes(b'second')
    [complete] = inventory(cfg, hub, punkt)['snapshots']
    assert complete['missing_standard_inputs'] == []
    assert complete['files']['part2']['sha256'] == hashlib.sha256(b'second').hexdigest()


def test_recheck_rejects_changed_bytes_and_missing_resource(inputs, tmp_path, capsys):
    cfg, hub, model, punkt = inputs
    args = ['--config', str(cfg), '--hf-cache', str(hub), '--punkt-english', str(punkt)]
    assert main(args) == 0
    baseline = tmp_path / 'manifest.json'
    baseline.write_text(capsys.readouterr().out)
    assert main([*args, '--compare', str(baseline)]) == 0
    assert json.loads(capsys.readouterr().out)['matches_local_inventory']
    (model / 'tokenizer.json').write_bytes(b'[]')
    assert main([*args, '--compare', str(baseline)]) == 1
    (model / 'tokenizer.json').write_bytes(b'{}')
    (punkt / 'abbrev_types.txt').unlink()
    assert main([*args, '--compare', str(baseline)]) == 1
    assert inventory(cfg, hub, punkt)['punkt_tab_english']['missing_tables'] == ['abbrev_types.txt']


def test_external_file_link_not_inventoried(inputs, tmp_path):
    cfg, hub, model, punkt = inputs
    external = tmp_path / 'external'
    external.write_bytes(b'not part of cache')
    try:
        (model / 'linked').symlink_to(external)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='redirected entry'):
        inventory(cfg, hub, punkt)
