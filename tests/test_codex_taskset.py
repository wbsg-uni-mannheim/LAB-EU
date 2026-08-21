"""Pure tests for the Codex ephemeral taskset runner."""

from __future__ import annotations

import argparse
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_codex_taskset import (  # noqa: E402
    build_codex_command,
    classify_codex_attempt,
    copy_anonymized_task,
    error_text,
    render_prompt,
    solver_configuration,
)


def args(**overrides) -> argparse.Namespace:
    values = {
        "codex_bin": "codex",
        "tool_access": "full",
        "with_memories": False,
        "model": "",
        "reasoning_effort": None,
        "blocked_domains": ["zjs-online.com"],
        "web_search_enabled": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_command_is_ephemeral_live_search_and_non_project(tmp_path):
    final = tmp_path / ".codex-final-message.md"
    command = build_codex_command(args(), tmp_path, final)

    assert command[:2] == ["codex", "--search"]
    assert command[command.index("--sandbox") + 1] == "danger-full-access"
    assert ["--ask-for-approval", "never"] == command[
        command.index("--ask-for-approval") : command.index("--ask-for-approval") + 2
    ]
    assert ["--disable", "memories"] == command[
        command.index("--disable") : command.index("--disable") + 2
    ]
    assert command[command.index("--cd") + 1] == str(tmp_path)
    assert "--ephemeral" in command
    assert "--skip-git-repo-check" in command
    assert command[-1] == "-"


def test_workspace_mode_and_explicit_model(tmp_path):
    command = build_codex_command(
        args(tool_access="workspace", model="gpt-test", reasoning_effort="high"),
        tmp_path,
        tmp_path / "final.md",
    )

    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert command[command.index("--model") + 1] == "gpt-test"
    assert 'model_reasoning_effort="high"' in command


def test_no_web_command_explicitly_disables_search(tmp_path):
    command = build_codex_command(
        args(tool_access="workspace", web_search_enabled=False),
        tmp_path,
        tmp_path / "final.md",
    )

    assert "--search" not in command
    assert 'web_search="disabled"' in command
    assert command[command.index("--sandbox") + 1] == "workspace-write"


def test_solver_configuration_records_pinned_reasoning_level():
    configuration = solver_configuration(
        args(model="gpt-5.6-sol", reasoning_effort="medium")
    )

    assert configuration["model"] == "gpt-5.6-sol"
    assert configuration["reasoning_effort"] == "medium"
    assert configuration["model_source"] == "cli-override"
    assert configuration["reasoning_effort_source"] == "cli-override"


def test_memories_can_be_explicitly_reenabled(tmp_path):
    command = build_codex_command(
        args(with_memories=True), tmp_path, tmp_path / "final.md"
    )
    assert "--disable" not in command


def test_solver_prompt_blocks_zjs_and_requires_negative_search_filter(tmp_path):
    (tmp_path / "task.json").write_text("{}", encoding="utf-8")
    prompt = render_prompt(
        args(),
        {
            "task_id": "case",
            "solver_case_id": "case-001",
            "task": {"title": "Case", "instructions": "Solve."},
            "deliverables": ["answer.md"],
        },
        tmp_path,
    )

    assert "- zjs-online.com" in prompt
    assert "-site:blocked.example" in prompt
    assert "Do not search, open, fetch, cite, or use" in prompt
    assert "No domain allowlist applies" in prompt
    assert "case-001" in prompt
    assert "Task title:\nJuristische Fallbearbeitung" in prompt
    assert "Task title:\nCase" not in prompt


def test_no_web_prompt_prohibits_all_external_research(tmp_path):
    (tmp_path / "task.json").write_text("{}", encoding="utf-8")
    prompt = render_prompt(
        args(web_search_enabled=False),
        {
            "task_id": "hidden-title",
            "solver_case_id": "case-001",
            "task": {"title": "Hidden", "instructions": "Solve."},
            "deliverables": ["answer.md"],
        },
        tmp_path,
    )

    assert "External web and network research is disabled" in prompt
    assert "cached search" in prompt
    assert "empty `sources` list" in prompt
    assert "Live web research is enabled" not in prompt


def test_anonymized_workspace_omits_identity_and_provenance(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "workspace"
    (source / "documents").mkdir(parents=True)
    (source / "documents" / "sachverhalt.md").write_text(
        "# Sachverhalt\n\nDie Fakten bleiben vollständig erhalten.\n",
        encoding="utf-8",
    )
    row = {
        "task_id": "de/examensubungsklausur-falsche-liebe",
        "solver_case_id": "case-001",
        "task_dir": source,
        "task": {
            "title": "Examensübungsklausur: Falsche Liebe",
            "work_type": "draft",
            "instructions": "Bearbeiten Sie den Fall gutachterlich.",
            "deliverables": "fallloesung.md",
            "tags": ["zjs", "ZJS_2022_1_S63"],
            "source": {"fundstelle": "ZJS_2022_1_S63", "autoren": "A und B"},
            "license": "Provenienztext",
        },
        "deliverables": ["fallloesung.md"],
    }

    copy_anonymized_task(row, destination)

    import json

    exposed = json.loads((destination / "task.json").read_text(encoding="utf-8"))
    # The exam format survives -- the rubric grades against its depth conventions --
    # while the case name, Fundstelle, authors and tags do not.
    assert exposed == {
        "title": "Examensübungsklausur",
        "work_type": "draft",
        "instructions": "Bearbeiten Sie den Fall gutachterlich.",
        "deliverables": ["fallloesung.md"],
    }
    written = (destination / "task.json").read_text(encoding="utf-8")
    assert "ZJS" not in written
    assert "Falsche Liebe" not in written
    assert (
        (destination / "documents" / "sachverhalt.md")
        .read_text(encoding="utf-8")
        .endswith("Die Fakten bleiben vollständig erhalten.\n")
    )


def test_normal_legal_answer_is_not_classified_as_http_error(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    stderr = tmp_path / "stderr.log"
    stdout.write_text(
        '{"type":"item.completed","item":{"type":"agent_message",'
        '"text":"Ein Anspruch aus § 404 BGB besteht."}}\n',
        encoding="utf-8",
    )
    stderr.write_text("", encoding="utf-8")

    assert error_text(stdout, stderr) == ""


def test_codex_error_event_is_available_to_retry_classifier(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    stderr = tmp_path / "stderr.log"
    stdout.write_text(
        '{"type":"error","message":"503 Service Unavailable"}\n', encoding="utf-8"
    )
    stderr.write_text("", encoding="utf-8")

    assert "503 Service Unavailable" in error_text(stdout, stderr)


def test_written_deliverable_wins_over_final_stream_disconnect():
    outcome, reason = classify_codex_attempt(
        exit_code=1,
        timed_out=False,
        missing_deliverables=False,
        diagnostics="connection closed",
    )

    assert outcome == "ok"
    assert reason == "deliverable captured"


def test_multi_deliverable_prompt_lists_every_file(tmp_path):
    (tmp_path / "task.json").write_text("{}", encoding="utf-8")
    prompt = render_prompt(
        args(),
        {
            "task_id": "case",
            "solver_case_id": "case-001",
            "task": {"title": "Case", "instructions": "Solve."},
            "deliverables": [
                "klageerwiderung-sut.md",
                "mandantenschreiben-sut.md",
                "hilfsgutachten-sut.md",
            ],
        },
        tmp_path,
    )

    assert "- klageerwiderung-sut.md" in prompt
    assert "- mandantenschreiben-sut.md" in prompt
    assert "- hilfsgutachten-sut.md" in prompt
    assert "every file is mandatory" in prompt
    assert "completion report" in prompt
    assert "Gutachtenstil for a Gutachten or Hilfsgutachten" in prompt
    assert "anwaltlicher Schriftsatzstil" in prompt
    assert "{deliverable" not in prompt


def test_single_deliverable_prompt_keeps_fallback_contract(tmp_path):
    (tmp_path / "task.json").write_text("{}", encoding="utf-8")
    prompt = render_prompt(
        args(),
        {
            "task_id": "case",
            "solver_case_id": "case-001",
            "task": {"title": "Case", "instructions": "Solve."},
            "deliverables": ["answer.md"],
        },
        tmp_path,
    )

    assert 'exactly "answer.md"' in prompt
    assert "fallback if the file write fails" in prompt
    assert "completion report" not in prompt


def multi_row(workspace: pathlib.Path) -> dict:
    (workspace / "task.json").write_text("{}", encoding="utf-8")
    (workspace / "documents").mkdir(exist_ok=True)
    (workspace / "documents" / "sachverhalt.md").write_text("Fakten", encoding="utf-8")
    return {
        "task_id": "case",
        "solver_case_id": "case-001",
        "task": {},
        "deliverables": ["urteil-sut.md", "hilfsgutachten-sut.md"],
    }


def test_copy_attempt_artifacts_complete_multi_submission(tmp_path):
    from run_codex_taskset import copy_attempt_artifacts

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    row = multi_row(workspace)
    (workspace / "urteil-sut.md").write_text("Urteil", encoding="utf-8")
    (workspace / "hilfsgutachten-sut.md").write_text("Gutachten", encoding="utf-8")
    task_run_dir = tmp_path / "run"
    task_run_dir.mkdir()

    results, fallback, unexpected = copy_attempt_artifacts(
        workspace, task_run_dir, workspace / ".codex-final-message.md", row
    )

    assert all(item["found"] for item in results)
    assert not fallback
    assert unexpected == []
    assert (task_run_dir / "submission" / "urteil-sut.md").read_text(
        encoding="utf-8"
    ) == "Urteil"
    assert (task_run_dir / "submission" / "hilfsgutachten-sut.md").is_file()


def test_copy_attempt_artifacts_reports_missing_and_wrong_named_files(tmp_path):
    from run_codex_taskset import copy_attempt_artifacts

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    row = multi_row(workspace)
    (workspace / "urteil-sut.md").write_text("Urteil", encoding="utf-8")
    (workspace / "hilfsgutachten.md").write_text("falscher Name", encoding="utf-8")
    final_message = workspace / ".codex-final-message.md"
    final_message.write_text("Ich habe die Dateien geschrieben.", encoding="utf-8")
    task_run_dir = tmp_path / "run"
    task_run_dir.mkdir()

    results, fallback, unexpected = copy_attempt_artifacts(
        workspace, task_run_dir, final_message, row
    )

    by_name = {item["path"]: item for item in results}
    assert by_name["urteil-sut.md"]["found"] is True
    assert by_name["hilfsgutachten-sut.md"]["found"] is False
    assert not fallback
    assert [item["path"] for item in unexpected] == ["hilfsgutachten.md"]
    assert not (task_run_dir / "submission" / "hilfsgutachten-sut.md").exists()


def test_final_message_fallback_stays_single_file_only(tmp_path):
    from run_codex_taskset import copy_attempt_artifacts

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    row = multi_row(workspace)
    final_message = workspace / ".codex-final-message.md"
    final_message.write_text("Volltext der Antwort", encoding="utf-8")
    task_run_dir = tmp_path / "run"
    task_run_dir.mkdir()

    results, fallback, _unexpected = copy_attempt_artifacts(
        workspace, task_run_dir, final_message, row
    )

    assert all(not item["found"] for item in results)
    assert not fallback


def test_unexpected_files_ignore_inputs_and_dotfiles(tmp_path):
    from run_codex_taskset import find_unexpected_files

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    row = multi_row(workspace)
    (workspace / "urteil-sut.md").write_text("Urteil", encoding="utf-8")
    (workspace / ".codex-used-sources.json").write_text('{"sources":[]}', encoding="utf-8")
    (workspace / "notizen.md").write_text("Zwischenstand", encoding="utf-8")

    unexpected = find_unexpected_files(workspace, row["deliverables"])

    assert [item["path"] for item in unexpected] == ["notizen.md"]
