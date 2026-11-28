from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from harness import gates


def _cfg(tasks=("arc_challenge",), num_fewshot=5, seeds=(0, 1, 2)):
    return {
        "model": {"id": "Qwen/Qwen3.5-0.8B", "revision": "2fc06364", "dtype": "bfloat16"},
        "capability": {"tasks": list(tasks), "num_fewshot": num_fewshot},
        "seeds": {"capability": list(seeds)},
    }


def test_command_carries_the_registered_seed():
    seeds = [_cfg()["seeds"]["capability"][i] for i in range(3)]
    commands = [gates._capability_command(_cfg(), Path("out"), seed) for seed in seeds]
    passed = [c[c.index("--seed") + 1] for c in commands]
    assert passed == ["0", "1", "2"]
    assert len({tuple(c) for c in commands}) == 3
    assert commands[0][commands[0].index("--tasks") + 1] == "arc_challenge"


def test_command_omits_seed_when_none_is_declared():
    assert "--seed" not in gates._capability_command(_cfg(), Path("out"), None)


def test_seed_spread_is_mean_and_sample_sd_not_lm_eval_stderr():
    per_seed = {
        "0": {"arc_challenge": {"acc,none": 0.2, "acc_stderr,none": 0.01}},
        "1": {"arc_challenge": {"acc,none": 0.4, "acc_stderr,none": 0.02}},
        "2": {"arc_challenge": {"acc,none": 0.6, "acc_stderr,none": 0.03}},
    }
    result = gates._capability_across_seeds(per_seed)
    assert result["mean"]["arc_challenge"] == {"acc,none": pytest.approx(0.4)}
    assert result["sd"]["arc_challenge"] == {"acc,none": pytest.approx(0.2)}
    assert "acc_stderr,none" not in result["mean"]["arc_challenge"]


def test_single_seed_reports_no_spread():
    result = gates._capability_across_seeds({"0": {"arc_challenge": {"acc,none": 0.4}}})
    assert result["sd"]["arc_challenge"] == {"acc,none": None}


def test_missing_metric_in_one_seed_is_refused():
    per_seed = {"0": {"arc_challenge": {"acc,none": 0.4}}, "1": {"arc_challenge": {}}}
    with pytest.raises(gates.ExecutionError, match="missing"):
        gates._capability_across_seeds(per_seed)


def test_gate_runs_every_seed_and_saves_aggregate(tmp_path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "harness.json").write_text(json.dumps(_cfg()), encoding="utf-8")
    calls = []

    class FakePopen:
        def __init__(self, command, **kwargs):
            self.seed = command[command.index("--seed") + 1]
            out = Path(command[command.index("--output_path") + 1])
            (out / "hf").mkdir(parents=True, exist_ok=True)
            (out / "hf" / "results_2026.json").write_text(
                json.dumps({"results": {"arc_challenge": {"acc,none": int(self.seed) / 10, "acc_stderr,none": 0.01}}}),
                encoding="utf-8",
            )
            calls.append(self.seed)
            self.returncode = 0

        def communicate(self):
            return f"seed {self.seed}", ""

        def poll(self):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(gates, "require_admitted", lambda run_dir: None)
    monkeypatch.setattr(gates.subprocess, "Popen", FakePopen)

    returned = gates.check_capability_suite(run_dir)

    assert returned["passed"] and returned["seeds"] == ["0", "1", "2"]
    saved = json.loads((run_dir / "results" / "capability_suite.json").read_text(encoding="utf-8"))
    assert saved["mean"]["arc_challenge"]["acc,none"] == pytest.approx(0.1)
    assert saved["sd"]["arc_challenge"]["acc,none"] == pytest.approx(0.1)
    assert sorted(saved["per_seed"]) == ["0", "1", "2"]


def test_failed_seed_keeps_its_logs_and_names_the_seed(tmp_path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "harness.json").write_text(json.dumps(_cfg(seeds=(0, 1))), encoding="utf-8")

    class FakePopen:
        def __init__(self, command, **kwargs):
            self.seed = command[command.index("--seed") + 1]
            if self.seed != "1":
                out = Path(command[command.index("--output_path") + 1])
                (out / "hf").mkdir(parents=True, exist_ok=True)
                (out / "hf" / "results_2026.json").write_text(
                    json.dumps({"results": {"arc_challenge": {"acc,none": 0.5}}}), encoding="utf-8",
                )
            self.returncode = 1 if self.seed == "1" else 0

        def communicate(self):
            return "", "boom 1" if self.seed == "1" else ""

        def poll(self):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(gates, "require_admitted", lambda run_dir: None)
    monkeypatch.setattr(gates.subprocess, "Popen", FakePopen)

    returned = gates.check_capability_suite(run_dir)

    assert returned["passed"] is False and returned["seed"] == "1"
    assert "boom 1" in returned["stderr_tail"]
