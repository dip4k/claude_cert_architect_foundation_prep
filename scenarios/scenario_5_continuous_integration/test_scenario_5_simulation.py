"""
Unit tests for Scenario 5: Claude Code for Continuous Integration simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_5_continuous_integration.simulation import (
    ContinuousIntegrationEngine,
    WorkloadType,
)


def test_ci_engine_requires_headless_flag():
    engine = ContinuousIntegrationEngine(headless_flag_present=False)
    with pytest.raises(RuntimeError) as exc:
        engine.run_two_pass_review({"app.py": "x = 1"})
    assert "-p" in str(exc.value)


def test_ci_engine_routes_blocking_pr_to_realtime_api():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    api = engine.route_api_for_workload(WorkloadType.BLOCKING_PR_CHECK)
    assert api == "REALTIME_MESSAGES"


def test_ci_engine_routes_overnight_audit_to_batch_api():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    api = engine.route_api_for_workload(WorkloadType.OVERNIGHT_REPO_AUDIT)
    assert api == "MESSAGE_BATCHES"


def test_ci_engine_two_pass_review_blocks_on_contract_mismatch():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    pr_files = {
        "api/routes.py": "def handle(bearer_token: str): pass",
        "client/sdk.py": "def call(): return handle(auth_token='abc')"
    }
    report = engine.run_two_pass_review(pr_files)
    assert report.exit_code == 1
    assert report.status == "CHANGES_REQUESTED"
    assert any(f.pass_number == 2 for f in report.findings)
    assert any(f.rule_id == "ARCH_003_CONTRACT_MISMATCH" for f in report.findings)


def test_ci_engine_negative_boundary_ignores_test_mock_keys():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    clean_pr = {
        "src/app.py": "def healthy(): return True",
        "tests/test_app.py": "mock_secret = 'sk-ant-live_fake_in_tests'"
    }
    report = engine.run_two_pass_review(clean_pr)
    assert report.exit_code == 0
    assert report.status == "APPROVED"


def test_ci_engine_catches_silent_exception_swallowing_in_pass_1():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    pr = {
        "src/worker.py": "try:\n    do_work()\nexcept Exception: pass\n"
    }
    report = engine.run_two_pass_review(pr)
    assert report.exit_code == 1
    assert any(f.rule_id == "ERR_002_SILENT_EXCEPTION" for f in report.findings)


def test_ci_engine_catches_production_secret_leak_in_source_code():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    pr = {
        "src/config.py": "ANTHROPIC_KEY = 'sk-ant-live-real-secret-12345'"
    }
    report = engine.run_two_pass_review(pr)
    assert report.exit_code == 1
    assert any(f.rule_id == "SEC_001_HARDCODED_KEY" for f in report.findings)


def test_ci_engine_catches_cross_file_breaking_deletion():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    pr = {
        "services/account.py": "class AccountService:\n- def get_account(uid: str): pass\n+ def get_account_by_id(uid: str): pass",
        "services/billing.py": "def charge():\n    acc = AccountService.get_account('u123')\n    return acc.balance"
    }
    report = engine.run_two_pass_review(pr)
    assert report.exit_code == 1
    assert any(f.rule_id == "ARCH_004_BREAKING_DELETION" for f in report.findings)


def test_ci_engine_distinguishes_identical_method_names_across_namespaces():
    engine = ContinuousIntegrationEngine(headless_flag_present=True)
    # Auth deletes 'verify', but Billing defines its own 'verify' and calls its own method
    pr = {
        "services/auth.py": "class AuthService:\n- def verify(token: str): pass",
        "services/billing.py": "class BillingService:\n+ def verify(charge_id: str): pass\ndef run():\n    return verify('c1')"
    }
    report = engine.run_two_pass_review(pr)
    # Should not flag a breaking deletion for BillingService calling its own added verify
    assert not any(f.rule_id == "ARCH_004_BREAKING_DELETION" and "BillingService" in f.description for f in report.findings)


