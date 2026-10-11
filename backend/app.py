"""
University Examination Scheduling Using Graphs
Backend Service (Flask)

This module acts as the bridge between the web interface and the compiled C
scheduling engine. It validates inputs, invokes the C executable via subprocess,
verifies that no conflicts share a slot, and returns the timetable as JSON.
"""

import os
import subprocess
import shutil
from flask import Flask, request, jsonify, send_from_directory

# Base directories resolved relative to this file
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
C_ENGINE_DIR = os.path.join(PROJECT_ROOT, "c_engine")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Name of the C binary depending on operating system (or overridden by SCHEDULER_BIN)
DEFAULT_BINARY_NAME = "scheduler.exe" if os.name == "nt" else "scheduler"
C_EXECUTABLE_PATH = os.environ.get("SCHEDULER_BIN", os.path.join(C_ENGINE_DIR, DEFAULT_BINARY_NAME))
C_SOURCE_PATH = os.path.join(C_ENGINE_DIR, "scheduler.c")

app = Flask(__name__, static_folder=FRONTEND_DIR)


def ensure_c_executable():
    """
    Checks if the C scheduling engine binary exists.
    If not, attempts to compile it automatically using gcc if available.
    Returns (executable_path, None) on success or (None, error_message).
    """
    if os.path.isfile(C_EXECUTABLE_PATH):
        # On POSIX/Linux, ensure execute permission is granted
        if os.name != "nt" and not os.access(C_EXECUTABLE_PATH, os.X_OK):
            try:
                os.chmod(C_EXECUTABLE_PATH, 0o755)
            except Exception:
                pass
        if os.access(C_EXECUTABLE_PATH, os.X_OK | os.R_OK):
            return C_EXECUTABLE_PATH, None

    # If binary does not exist, check for C source file
    if not os.path.isfile(C_SOURCE_PATH):
        return None, f"C source file not found at {C_SOURCE_PATH}"

    # Try to find gcc in PATH
    gcc_path = shutil.which("gcc")
    if not gcc_path:
        return None, (
            "C scheduler binary is missing and GCC was not found on PATH. "
            f"Please compile {C_SOURCE_PATH} manually to {C_EXECUTABLE_PATH}."
        )

    # Attempt automatic compilation
    compile_cmd = [
        gcc_path,
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-O2",
        C_SOURCE_PATH,
        "-o",
        C_EXECUTABLE_PATH,
    ]
    try:
        res = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return None, f"Failed to compile C scheduler: {res.stderr.strip()}"
    except Exception as e:
        return None, f"Error compiling C scheduler: {str(e)}"

    if os.path.isfile(C_EXECUTABLE_PATH):
        return C_EXECUTABLE_PATH, None
    return None, f"Compiled binary not found at {C_EXECUTABLE_PATH}"


@app.route("/")
def serve_index():
    """Serves the main single-page web interface."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_static_file(path):
    """Serves static assets (CSS, JS) from the frontend folder."""
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/schedule", methods=["POST"])
def schedule_exams():
    """
    API endpoint: POST /api/schedule
    
    Expected JSON payload:
    {
      "subjects": ["Mathematics", "Physics", ...],
      "conflicts": [[0, 1], [0, 2], ...]
    }
    """
    # 1. Parse and validate JSON request
    if not request.is_json:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"success": False, "error": "Malformed JSON payload."}), 400

    # 2. Validate "subjects" field
    if "subjects" not in data:
        return jsonify({"success": False, "error": "Missing required field: 'subjects'."}), 400

    subjects = data["subjects"]
    if not isinstance(subjects, list):
        return jsonify({"success": False, "error": "'subjects' must be a list of subject names."}), 400

    num_subjects = len(subjects)
    if num_subjects < 1:
        return jsonify({"success": False, "error": "At least 1 subject is required."}), 400

    if num_subjects > 20:
        return jsonify({"success": False, "error": "A maximum of 20 subjects is supported."}), 400

    cleaned_subjects = []
    seen_names = set()
    for idx, s in enumerate(subjects):
        if not isinstance(s, str):
            return jsonify({"success": False, "error": f"Subject at index {idx} must be a string."}), 400
        trimmed = s.strip()
        if not trimmed:
            return jsonify({"success": False, "error": f"Subject at index {idx} cannot be empty."}), 400
        if len(trimmed) > 80:
            return jsonify({"success": False, "error": f"Subject name '{trimmed[:20]}...' exceeds 80 characters."}), 400
        if trimmed.lower() in seen_names:
            return jsonify({"success": False, "error": f"Duplicate subject name detected: '{trimmed}'."}), 400
        seen_names.add(trimmed.lower())
        cleaned_subjects.append(trimmed)

    # 3. Validate "conflicts" field
    if "conflicts" not in data:
        return jsonify({"success": False, "error": "Missing required field: 'conflicts'."}), 400

    conflicts = data["conflicts"]
    if not isinstance(conflicts, list):
        return jsonify({"success": False, "error": "'conflicts' must be a list of subject index pairs."}), 400

    max_conflicts = (num_subjects * (num_subjects - 1)) // 2
    if len(conflicts) > max_conflicts:
        return jsonify({
            "success": False,
            "error": f"Too many conflicts. Maximum possible for {num_subjects} subjects is {max_conflicts}."
        }), 400

    cleaned_conflicts = []
    seen_edges = set()
    for idx, pair in enumerate(conflicts):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return jsonify({"success": False, "error": f"Conflict item at index {idx} must be a pair [u, v]."}), 400

        u, v = pair[0], pair[1]
        # Ensure indices are integers and not booleans (isinstance(True, int) is True in Python)
        if isinstance(u, bool) or not isinstance(u, int) or isinstance(v, bool) or not isinstance(v, int):
            return jsonify({"success": False, "error": f"Conflict indices at index {idx} must be integers."}), 400

        if u < 0 or u >= num_subjects:
            return jsonify({"success": False, "error": f"Subject index {u} in conflict {idx} is out of bounds (0 to {num_subjects - 1})."}), 400

        if v < 0 or v >= num_subjects:
            return jsonify({"success": False, "error": f"Subject index {v} in conflict {idx} is out of bounds (0 to {num_subjects - 1})."}), 400

        if u == v:
            return jsonify({"success": False, "error": "A subject cannot conflict with itself."}), 400

        # Undirected edge representation (u < v)
        edge = (min(u, v), max(u, v))
        if edge in seen_edges:
            return jsonify({
                "success": False,
                "error": f"Duplicate conflict pair between '{cleaned_subjects[edge[0]]}' and '{cleaned_subjects[edge[1]]}'."
            }), 400
        seen_edges.add(edge)
        cleaned_conflicts.append(edge)

    # 4. Ensure C executable is present
    executable_path, err = ensure_c_executable()
    if err or not executable_path:
        return jsonify({"success": False, "error": err or "C engine executable unavailable."}), 500

    # 5. Format input protocol for C engine:
    #    Line 1: N
    #    Line 2: E
    #    Next E lines: a b (1-based indices)
    input_lines = [str(num_subjects), str(len(cleaned_conflicts))]
    for u, v in cleaned_conflicts:
        input_lines.append(f"{u + 1} {v + 1}")
    c_input_str = "\n".join(input_lines) + "\n"

    # 6. Execute C scheduling engine using subprocess
    try:
        proc = subprocess.run(
            [executable_path],
            input=c_input_str,
            capture_output=True,
            text=True,
            timeout=5.0,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "C scheduling engine timed out."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Error running C scheduling engine: {str(e)}"}), 500

    if proc.returncode != 0:
        stderr_msg = proc.stderr.strip() if proc.stderr else "Nonzero exit code from C engine."
        return jsonify({"success": False, "error": f"C engine error: {stderr_msg}"}), 500

    # 7. Parse output from C engine
    #    Expected:
    #    Line 1: Total slots (K)
    #    Next N lines: 1-based slot assignment for each subject
    stdout_tokens = proc.stdout.strip().split()
    if len(stdout_tokens) != (1 + num_subjects):
        return jsonify({
            "success": False,
            "error": f"Unexpected C engine output format. Expected {1 + num_subjects} values, received {len(stdout_tokens)}."
        }), 500

    try:
        total_slots = int(stdout_tokens[0])
        assigned_slots = [int(token) for token in stdout_tokens[1:]]
    except ValueError:
        return jsonify({"success": False, "error": "C engine returned non-integer slot numbers."}), 500

    if total_slots < 1 or total_slots > num_subjects:
        return jsonify({"success": False, "error": f"Invalid total slots returned by C engine: {total_slots}."}), 500

    for s in assigned_slots:
        if s < 1 or s > total_slots:
            return jsonify({"success": False, "error": f"Assigned slot {s} is outside valid range [1, {total_slots}]."}), 500

    # 8. Post-verification: ensure no conflicting subjects share the same slot
    for u, v in cleaned_conflicts:
        if assigned_slots[u] == assigned_slots[v]:
            return jsonify({
                "success": False,
                "error": (
                    f"Conflict verification failed: '{cleaned_subjects[u]}' and "
                    f"'{cleaned_subjects[v]}' both assigned to Slot {assigned_slots[u]}."
                )
            }), 500

    # 9. Structure final JSON response
    #    schedule: preserves input order
    #    slots: grouped by slot number 1..total_slots
    schedule = []
    for i, subj in enumerate(cleaned_subjects):
        schedule.append({
            "subject": subj,
            "slot": assigned_slots[i]
        })

    slots_grouped = []
    for s in range(1, total_slots + 1):
        subjects_in_slot = [cleaned_subjects[i] for i in range(num_subjects) if assigned_slots[i] == s]
        slots_grouped.append({
            "slot": s,
            "subjects": subjects_in_slot
        })

    return jsonify({
        "success": True,
        "total_slots": total_slots,
        "schedule": schedule,
        "slots": slots_grouped
    }), 200


# Check and log C scheduling engine on startup/import (useful for Gunicorn)
_init_bin, _init_err = ensure_c_executable()
if _init_err:
    print(f"[Warning on startup] {_init_err}")
else:
    print(f"[Info on startup] C scheduling engine ready at: {_init_bin}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[Info] Starting University Examination Scheduler on http://{host}:{port} ...")
    app.run(host=host, port=port)

