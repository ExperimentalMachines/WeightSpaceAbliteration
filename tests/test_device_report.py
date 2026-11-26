from __future__ import annotations

from harness.device import Device, detect, environment_profile, report


def test_cpu_device_on_this_host():
    # CI and laptops without an accelerator still produce a coherent report.
    device = detect()
    assert device.backend in ("cpu", "cuda", "rocm")
    assert device.torch


def test_report_keys():
    r = report()
    assert set(r) == {"device", "dtypes", "sdpa", "attention_backends", "environment"}


def test_rocm_env_splits_arithmetic():
    device = Device("rocm", 0, "MI300X", "gfx942", 192.0, "2.15.0+rocm6.4", "6.4.0", "aotriton")
    env = environment_profile(device)
    assert "HIP_FORCE_DEV_KERNARG" in env["arithmetic_neutral"]
    assert "TORCH_BLAS_PREFER_HIPBLASLT" in env["may_change_arithmetic"]
    assert "TORCH_ROCM_FA_PREFER_CK" in env["may_change_arithmetic"]


def test_nvidia_env_is_empty():
    device = Device("cuda", 0, "A100", "sm_80", 40.0, "2.15.0+cu132", "13.2", None)
    env = environment_profile(device)
    assert env == {"arithmetic_neutral": {}, "may_change_arithmetic": {}}


def test_vendor_probes_filter_by_availability(monkeypatch):
    from scripts import record_host as rh

    present = {"nvidia-smi"}
    monkeypatch.setattr("shutil.which", lambda tool: "/usr/bin/" + tool if tool in present else None)
    probes = rh._vendor_probes()
    assert len(probes) == 1
    assert probes[0][0] == "nvidia-smi"


def test_vendor_probes_includes_amd_when_found(monkeypatch):
    from scripts import record_host as rh

    present = {"amd-smi", "rocm-smi"}
    monkeypatch.setattr("shutil.which", lambda tool: "/opt/rocm/bin/" + tool if tool in present else None)
    probes = rh._vendor_probes()
    assert len(probes) == 2
    assert any(p[0] == "amd-smi" for p in probes)
    assert any(p[0] == "rocm-smi" for p in probes)
