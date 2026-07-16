"""Flask application factory for the local lawyer workbench."""

from __future__ import annotations

import pathlib
import secrets

from flask import Flask, jsonify, render_template, request

from .core import (
    RUNS_ROOT,
    STUDIES_ROOT,
    WorkbenchError,
    create_manual_run,
    create_study,
    default_study_system_prompt,
    discover_tasks,
    end_study_early,
    get_task,
    git_readiness,
    list_studies,
    save_study_answer,
    study_payload,
    submit_manual_run,
    task_payload,
)


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        WORKBENCH_TOKEN=secrets.token_urlsafe(24),
        RUNS_ROOT=RUNS_ROOT,
        STUDIES_ROOT=STUDIES_ROOT,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if config:
        app.config.update(config)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            workbench_token=app.config["WORKBENCH_TOKEN"],
            default_system_prompt=default_study_system_prompt(),
        )

    @app.get("/api/tasks")
    def tasks():
        language = request.args.get("language", "").lower()
        records = discover_tasks()
        if language in {"de", "fr"}:
            records = [record for record in records if record.language == language]
        return jsonify({"tasks": [record.summary() for record in records]})

    @app.get("/api/task")
    def task():
        return jsonify(task_payload(get_task(request.args.get("task_id", ""))))

    @app.get("/api/studies")
    def studies():
        return jsonify({"studies": list_studies(pathlib.Path(app.config["STUDIES_ROOT"]))})

    @app.get("/api/studies/<study_id>")
    def study(study_id: str):
        return jsonify(study_payload(study_id, pathlib.Path(app.config["STUDIES_ROOT"])))

    def require_token() -> None:
        if request.headers.get("X-Workbench-Token") != app.config["WORKBENCH_TOKEN"]:
            raise WorkbenchError("Invalid workbench token. Reload the page.")

    @app.post("/api/runs")
    def save_run():
        require_token()
        data = request.get_json(silent=True) or {}
        if data.get("confidentiality_confirmed") is not True:
            raise WorkbenchError("Confirm that the response contains no confidential client data.")
        record = get_task(str(data.get("task_id", "")))
        result = create_manual_run(
            record=record,
            response=str(data.get("response", "")),
            reviewer=str(data.get("reviewer", "")),
            provider=str(data.get("provider", "")),
            model=str(data.get("model", "")),
            runs_root=pathlib.Path(app.config["RUNS_ROOT"]),
        )
        return jsonify(result), 201

    @app.post("/api/studies")
    def start_study():
        require_token()
        data = request.get_json(silent=True) or {}
        result = create_study(
            name=str(data.get("name", "")),
            model=str(data.get("model", "")),
            language=str(data.get("language", "")),
            system_prompt=str(data.get("system_prompt", "")),
            reviewer=str(data.get("reviewer", "")),
            provider=str(data.get("provider", "")),
            capabilities=data.get("capabilities") if isinstance(data.get("capabilities"), dict) else {},
            judge_ready_only=data.get("judge_ready_only") is True,
            studies_root=pathlib.Path(app.config["STUDIES_ROOT"]),
        )
        return jsonify(result), 201

    @app.post("/api/studies/<study_id>/answers")
    def save_study_result(study_id: str):
        require_token()
        data = request.get_json(silent=True) or {}
        return jsonify(
            save_study_answer(
                study_id=study_id,
                task_id=str(data.get("task_id", "")),
                response=str(data.get("response", "")),
                confidentiality_confirmed=data.get("confidentiality_confirmed") is True,
                studies_root=pathlib.Path(app.config["STUDIES_ROOT"]),
            )
        )

    @app.post("/api/studies/<study_id>/end-early")
    def submit_study_early(study_id: str):
        require_token()
        data = request.get_json(silent=True) or {}
        return jsonify(
            end_study_early(
                study_id=study_id,
                confirmed=data.get("confirmed") is True,
                studies_root=pathlib.Path(app.config["STUDIES_ROOT"]),
            )
        )

    @app.get("/api/git-status")
    def git_status():
        return jsonify(git_readiness(request.args.get("run_dir", "")))

    @app.post("/api/submit")
    def submit():
        require_token()
        data = request.get_json(silent=True) or {}
        if data.get("git_confirmed") is not True:
            raise WorkbenchError("Git submission requires explicit confirmation.")
        return jsonify(
            submit_manual_run(
                run_dir_relative=str(data.get("run_dir", "")),
                task_id=str(data.get("task_id", "")),
                reviewer=str(data.get("reviewer", "")),
                base_branch=str(data.get("base_branch", "main")),
                create_pull_request=data.get("create_pull_request") is True,
            )
        )

    @app.errorhandler(WorkbenchError)
    def handle_workbench_error(error: WorkbenchError):
        return jsonify({"error": str(error)}), 400

    return app
