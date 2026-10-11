"""
University Examination Scheduling Using Graphs
Automated Test Suite (C Engine, Flask Backend, and End-to-End Integration)

Tests cover:
- Section 9.1: C Engine unit and boundary tests
- Section 9.2: Flask API endpoint, validation, and error handling tests
- Section 9.3: Integration tests verifying conflict-free slot assignments
"""

import os
import sys
import subprocess
import unittest
import json
from unittest.mock import patch

# Add backend directory to sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
C_ENGINE_DIR = os.path.join(PROJECT_ROOT, "c_engine")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, ensure_c_executable, C_EXECUTABLE_PATH


class TestCEngine(unittest.TestCase):
    """Direct tests for the compiled standalone C scheduling engine."""

    @classmethod
    def setUpClass(cls):
        exe_path, err = ensure_c_executable()
        if err or not exe_path:
            raise RuntimeError(f"Cannot run C engine tests: {err}")
        cls.exe = exe_path

    def run_c_engine(self, input_str):
        """Helper to invoke C executable with given stdin."""
        return subprocess.run(
            [self.exe],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=5.0,
            shell=False,
        )

    def parse_success_output(self, proc):
        self.assertEqual(proc.returncode, 0, f"C engine failed unexpectedly with stderr: {proc.stderr}")
        tokens = proc.stdout.strip().split()
        total_slots = int(tokens[0])
        slots = [int(t) for t in tokens[1:]]
        return total_slots, slots

    def test_01_one_subject_no_conflicts(self):
        proc = self.run_c_engine("1\n0\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 1)
        self.assertEqual(slots, [1])

    def test_02_several_subjects_no_conflicts(self):
        # 4 subjects, 0 conflicts -> all can take slot 1
        proc = self.run_c_engine("4\n0\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 1)
        self.assertEqual(slots, [1, 1, 1, 1])

    def test_03_two_subjects_that_conflict(self):
        # 2 subjects, 1 conflict: (1, 2) -> need 2 slots
        proc = self.run_c_engine("2\n1\n1 2\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 2)
        self.assertNotEqual(slots[0], slots[1])

    def test_04_three_mutually_conflicting_subjects_k3(self):
        # Complete graph K3 -> 3 slots
        proc = self.run_c_engine("3\n3\n1 2\n1 3\n2 3\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 3)
        self.assertEqual(len(set(slots)), 3)

    def test_05_cycle_graph_c4_slot_sharing(self):
        # 4 subjects: 1-2, 2-3, 3-4, 4-1 (bipartite cycle C4)
        # Greedy coloring can achieve 2 slots
        proc = self.run_c_engine("4\n4\n1 2\n2 3\n3 4\n4 1\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 2)
        # Check no conflicting pair shares a slot
        conflicts = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for u, v in conflicts:
            self.assertNotEqual(slots[u], slots[v])

    def test_06_disconnected_graph(self):
        # 5 subjects: Component A: 1-2, Component B: 3-4, Component C: 5 isolated
        proc = self.run_c_engine("5\n2\n1 2\n3 4\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 2)
        self.assertNotEqual(slots[0], slots[1])
        self.assertNotEqual(slots[2], slots[3])

    def test_07_chain_path_graph(self):
        # 4 subjects: 1-2-3-4
        proc = self.run_c_engine("4\n3\n1 2\n2 3\n3 4\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 2)
        for u, v in [(0, 1), (1, 2), (2, 3)]:
            self.assertNotEqual(slots[u], slots[v])

    def test_08_max_supported_subjects_20(self):
        # 20 subjects, cycle among all 20
        edges = []
        for i in range(1, 20):
            edges.append(f"{i} {i + 1}")
        edges.append("20 1")
        input_str = f"20\n{len(edges)}\n" + "\n".join(edges) + "\n"
        proc = self.run_c_engine(input_str)
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(len(slots), 20)
        # Verify all adjacent edges have different colors
        for i in range(19):
            self.assertNotEqual(slots[i], slots[i + 1])
        self.assertNotEqual(slots[19], slots[0])

    def test_09_zero_conflicts(self):
        proc = self.run_c_engine("5\n0\n")
        total_slots, slots = self.parse_success_output(proc)
        self.assertEqual(total_slots, 1)
        self.assertEqual(slots, [1, 1, 1, 1, 1])

    def test_10_invalid_subject_counts(self):
        # 0 subjects
        proc0 = self.run_c_engine("0\n0\n")
        self.assertNotEqual(proc0.returncode, 0)
        self.assertIn("between 1 and 20", proc0.stderr)

        # -3 subjects
        procn = self.run_c_engine("-3\n0\n")
        self.assertNotEqual(procn.returncode, 0)

        # 21 subjects (> MAX_SUBJECTS)
        proc21 = self.run_c_engine("21\n0\n")
        self.assertNotEqual(proc21.returncode, 0)
        self.assertIn("between 1 and 20", proc21.stderr)

    def test_11_invalid_conflict_indices(self):
        # 0 index (1-based expected)
        proc0 = self.run_c_engine("3\n1\n0 1\n")
        self.assertNotEqual(proc0.returncode, 0)

        # N+1 index
        procout = self.run_c_engine("3\n1\n1 4\n")
        self.assertNotEqual(procout.returncode, 0)
        self.assertIn("out of bounds", procout.stderr)

    def test_12_self_conflicts(self):
        proc = self.run_c_engine("3\n1\n2 2\n")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Self-conflict", proc.stderr)

    def test_13_malformed_input(self):
        # Non-numeric subjects count
        proc_str = self.run_c_engine("three\n0\n")
        self.assertNotEqual(proc_str.returncode, 0)

        # Truncated conflicts (expects 3, only 1 provided)
        proc_trunc = self.run_c_engine("4\n3\n1 2\n")
        self.assertNotEqual(proc_trunc.returncode, 0)


class TestBackendAPI(unittest.TestCase):
    """Tests for the Flask API endpoint (/api/schedule) and input validation."""

    def setUp(self):
        self.client = app.test_client()

    def test_successful_schedule(self):
        payload = {
            "subjects": ["Math", "Physics", "Chemistry", "Biology"],
            "conflicts": [[0, 1], [1, 2], [2, 3]]
        }
        res = self.client.post("/api/schedule", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_slots"], 2)
        self.assertEqual(len(data["schedule"]), 4)
        self.assertEqual(len(data["slots"]), 2)

        # Verify subjects in schedule preserve order
        for idx, subj in enumerate(payload["subjects"]):
            self.assertEqual(data["schedule"][idx]["subject"], subj)

        # Verify conflicting pairs have different slots
        subj_slot = {item["subject"]: item["slot"] for item in data["schedule"]}
        self.assertNotEqual(subj_slot["Math"], subj_slot["Physics"])
        self.assertNotEqual(subj_slot["Physics"], subj_slot["Chemistry"])
        self.assertNotEqual(subj_slot["Chemistry"], subj_slot["Biology"])

    def test_missing_json_body(self):
        res = self.client.post("/api/schedule", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("valid JSON", data["error"])

    def test_missing_fields(self):
        # Missing conflicts
        res1 = self.client.post("/api/schedule", json={"subjects": ["Math"]})
        self.assertEqual(res1.status_code, 400)
        self.assertIn("conflicts", res1.get_json()["error"])

        # Missing subjects
        res2 = self.client.post("/api/schedule", json={"conflicts": []})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("subjects", res2.get_json()["error"])

    def test_empty_or_too_many_subjects(self):
        # Empty subjects list
        res_empty = self.client.post("/api/schedule", json={"subjects": [], "conflicts": []})
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("At least 1", res_empty.get_json()["error"])

        # 21 subjects
        res_21 = self.client.post("/api/schedule", json={
            "subjects": [f"S{i}" for i in range(21)],
            "conflicts": []
        })
        self.assertEqual(res_21.status_code, 400)
        self.assertIn("maximum of 20", res_21.get_json()["error"])

    def test_empty_and_duplicate_subject_names(self):
        # Whitespace-only subject name
        res_space = self.client.post("/api/schedule", json={
            "subjects": ["Math", "   "],
            "conflicts": []
        })
        self.assertEqual(res_space.status_code, 400)
        self.assertIn("cannot be empty", res_space.get_json()["error"])

        # Duplicate subject name
        res_dup = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics", "math"],
            "conflicts": []
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("Duplicate subject name", res_dup.get_json()["error"])

    def test_invalid_conflict_indices(self):
        # Index out of bounds
        res_oob = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics"],
            "conflicts": [[0, 2]]
        })
        self.assertEqual(res_oob.status_code, 400)
        self.assertIn("out of bounds", res_oob.get_json()["error"])

        # Negative index
        res_neg = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics"],
            "conflicts": [[-1, 1]]
        })
        self.assertEqual(res_neg.status_code, 400)
        self.assertIn("out of bounds", res_neg.get_json()["error"])

    def test_self_conflict(self):
        res_self = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics"],
            "conflicts": [[0, 0]]
        })
        self.assertEqual(res_self.status_code, 400)
        self.assertIn("cannot conflict with itself", res_self.get_json()["error"])

    def test_duplicate_conflict_pairs(self):
        # Duplicate direct and reversed
        res_dup = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics", "CS"],
            "conflicts": [[0, 1], [1, 0]]
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("Duplicate conflict pair", res_dup.get_json()["error"])

    def test_non_integer_conflict_indices(self):
        res_bool = self.client.post("/api/schedule", json={
            "subjects": ["Math", "Physics"],
            "conflicts": [[True, 1]]
        })
        self.assertEqual(res_bool.status_code, 400)
        self.assertIn("must be integers", res_bool.get_json()["error"])

    def test_missing_c_executable_handling(self):
        with patch("app.ensure_c_executable", return_value=(None, "Executable not found")):
            res = self.client.post("/api/schedule", json={
                "subjects": ["Math", "Physics"],
                "conflicts": [[0, 1]]
            })
            self.assertEqual(res.status_code, 500)
            self.assertFalse(res.get_json()["success"])
            self.assertIn("Executable not found", res.get_json()["error"])

    def test_c_engine_timeout_handling(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="scheduler", timeout=5.0)):
            res = self.client.post("/api/schedule", json={
                "subjects": ["Math", "Physics"],
                "conflicts": [[0, 1]]
            })
            self.assertEqual(res.status_code, 500)
            self.assertIn("timed out", res.get_json()["error"])

    def test_c_engine_malformed_output_handling(self):
        # Case 1: Wrong token count
        mock_proc_wrong_count = subprocess.CompletedProcess(
            args=["scheduler"], returncode=0, stdout="1\n", stderr=""
        )
        with patch("subprocess.run", return_value=mock_proc_wrong_count):
            res = self.client.post("/api/schedule", json={
                "subjects": ["Math", "Physics"],
                "conflicts": [[0, 1]]
            })
            self.assertEqual(res.status_code, 500)
            self.assertIn("output format", res.get_json()["error"])

        # Case 2: Non-integer tokens
        mock_proc_non_int = subprocess.CompletedProcess(
            args=["scheduler"], returncode=0, stdout="2\nX\nY\n", stderr=""
        )
        with patch("subprocess.run", return_value=mock_proc_non_int):
            res2 = self.client.post("/api/schedule", json={
                "subjects": ["Math", "Physics"],
                "conflicts": [[0, 1]]
            })
            self.assertEqual(res2.status_code, 500)
            self.assertIn("non-integer", res2.get_json()["error"])


class TestFrontendServing(unittest.TestCase):
    """Tests for serving frontend static assets."""

    def setUp(self):
        self.client = app.test_client()

    def test_serve_index_html(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"University Examination Scheduler", res.data)
        res.close()

    def test_serve_style_css(self):
        res = self.client.get("/style.css")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Academic Dashboard Theme", res.data)
        res.close()

    def test_serve_script_js(self):
        res = self.client.get("/script.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"University Examination Scheduler", res.data)
        res.close()


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration test: Client Request -> Flask API -> Real C binary -> Client Response."""

    def setUp(self):
        self.client = app.test_client()

    def test_realistic_university_exam_schedule(self):
        payload = {
            "subjects": [
                "Data Structures",
                "Operating Systems",
                "Discrete Math",
                "Computer Networks",
                "Database Systems"
            ],
            "conflicts": [
                [0, 1],  # DS & OS
                [0, 2],  # DS & Discrete Math
                [1, 2],  # OS & Discrete Math
                [2, 3],  # Discrete Math & Networks
                [3, 4]   # Networks & DBMS
            ]
        }
        res = self.client.post("/api/schedule", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["total_slots"], 1)
        self.assertEqual(len(data["schedule"]), 5)

        # Verify no conflicting pair has same slot
        subj_map = {item["subject"]: item["slot"] for item in data["schedule"]}
        for u, v in payload["conflicts"]:
            s_u = payload["subjects"][u]
            s_v = payload["subjects"][v]
            self.assertNotEqual(
                subj_map[s_u],
                subj_map[s_v],
                f"Conflicting subjects '{s_u}' and '{s_v}' share slot {subj_map[s_u]}"
            )

        # Verify slots grouping
        total_grouped_subjects = sum(len(group["subjects"]) for group in data["slots"])
        self.assertEqual(total_grouped_subjects, 5)


if __name__ == "__main__":
    unittest.main()
