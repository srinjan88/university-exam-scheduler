# University Examination Scheduling Using Graph Coloring

> **Data Structures and Algorithms (DSA) Mini Project**  
> A lightweight, beginner-friendly web application that schedules conflict-free university examination timetables using an adjacency matrix and greedy graph coloring in C, bridged with a Python Flask REST API and a vanilla JavaScript frontend.

---

## 1. Project Overview

At universities, scheduling final examinations is a major logistical challenge. If a student is enrolled in both *Mathematics* and *Physics*, those two exams cannot be held in the same examination time slot without causing an exam clash. 

This project models the university examination timetable problem as a classic **Graph Coloring Problem**:
- **Vertices (Nodes):** Examination subjects.
- **Edges:** Student enrollment conflicts (at least one student is enrolled in both subjects).
- **Colors:** Examination time slots (e.g., Slot 1, Slot 2, Slot 3...).
- **Rule:** No two adjacent vertices (conflicting subjects) can be assigned the same color (time slot).

The application pairs a **standalone, high-performance C scheduling engine** with a clean **Flask web backend** and an **academic dashboard frontend**.

---

## 2. Problem Statement & Objectives

### Problem Statement
Given $N$ examination subjects and a list of conflicting subject pairs, assign each subject an examination time slot such that:
1. No conflicting subjects share the same time slot.
2. The total number of required time slots is kept reasonably small.
3. The scheduling engine runs deterministically, quickly, and with strict input validation.

### Objectives
- Demonstrate the real-world application of **Graphs**, **Adjacency Matrices**, and **Greedy Graph Coloring**.
- Maintain clean modularity: the core DSA algorithm is implemented strictly in **C11**, while web interaction is handled cleanly via Python and standard web technologies.
- Provide a clear, educational, viva-ready explanation suitable for a first-year Computer Science student.

---

## 3. Data Structures & Algorithm Explanation

### 3.1 Graph Representation: 2D Adjacency Matrix

A graph can be represented in memory using either an *Adjacency List* or an *Adjacency Matrix*. For this project, a **Two-Dimensional Adjacency Matrix** is used:

```c
#define MAX_SUBJECTS 20
int graph[MAX_SUBJECTS][MAX_SUBJECTS];
```

#### How it Works:
1. Every subject is assigned a 0-based index from $0$ to $N - 1$.
2. All cells in `graph[MAX_SUBJECTS][MAX_SUBJECTS]` are initially set to `0` (indicating no conflict).
3. If subject $u$ and subject $v$ conflict, an undirected edge is recorded by setting:
   ```c
   graph[u][v] = 1;
   graph[v][u] = 1;
   ```
4. The matrix is **symmetric** across the main diagonal because conflict is mutual: if student $X$ takes both Subject $A$ and Subject $B$, $A$ conflicts with $B$ and $B$ conflicts with $A$.
5. **Self-conflicts** (`graph[i][i]`) are strictly disallowed, ensuring the diagonal remains `0`.

#### Complexity:
- **Space Complexity:** $\mathcal{O}(V^2)$, where $V \le 20$. In fixed memory, this consumes $20 \times 20 \times 4\text{ bytes} = 1600\text{ bytes}$—negligible and fast to allocate.
- **Edge Lookup Time:** $\mathcal{O}(1)$ constant time check to see if subject $u$ conflicts with subject $v$.

---

### 3.2 Greedy Graph Coloring Algorithm

Finding the absolute minimum number of colors for an arbitrary graph (the *chromatic number* $\chi(G)$) is an **NP-complete** problem. For practical scheduling, polynomial-time heuristic algorithms such as **Greedy Graph Coloring** are widely adopted.

#### Step-by-Step Algorithm:
1. Initialize an array `slots[MAX_SUBJECTS]` to `-1` for all subjects, indicating they are initially unassigned.
2. Initialize an auxiliary array `available[MAX_SUBJECTS]` where `1` denotes that a slot is free, and `0` denotes that it is occupied by an adjacent subject.
3. For each subject $u$ from $0$ to $N - 1$:
   - Mark all slots as available: set `available[c] = 1` for all $c \in [0, \text{MAX\_SUBJECTS}-1]$.
   - Check all adjacent subjects $v$:
     - For every subject $v$ where `graph[u][v] == 1` and `slots[v] != -1`:
       - Mark $v$'s assigned slot as unavailable: `available[slots[v]] = 0`.
   - Iterate through `available[]` to find the **smallest non-negative slot index** `c` where `available[c] == 1`.
   - Assign that slot to subject $u$: `slots[u] = c`.
4. Calculate the total number of slots used:
   $$\text{Total Slots} = \max(\text{slots}[0], \dots, \text{slots}[N - 1]) + 1$$
5. Convert internal 0-based slots to 1-based slots for user display.

#### Important Academic Note:
> **Is Greedy Graph Coloring always optimal?**  
> No. Greedy graph coloring depends on vertex ordering. While it is guaranteed to produce a **valid, conflict-free** schedule and will never use more than $\Delta(G) + 1$ colors (where $\Delta(G)$ is the maximum degree in the graph), it may not always find the globally minimal chromatic number for every possible graph.

#### Time Complexity:
- Outer loop runs $V$ times (for each subject).
- Inner loop inspects $V$ potential neighbors in the adjacency matrix.
- Total Time Complexity: $\mathcal{O}(V^2)$, which takes under a microsecond for $V \le 20$.

---

## 4. System Architecture

```
+-------------------------------------------------------------+
|                        Web Browser                          |
|         (HTML5 / Modern Responsive CSS3 / Vanilla JS)       |
+------------------------------+------------------------------+
                               |  JSON over HTTP (Fetch API)
                               v
+-------------------------------------------------------------+
|                     Flask Backend Service                   |
|                        (backend/app.py)                     |
|  - Validates JSON structure, subject names, conflict pairs   |
|  - Converts 0-based JSON indices to 1-based line protocol   |
|  - Invokes C executable via subprocess (shell=False)        |
|  - Performs safety verification on returned slots           |
+------------------------------+------------------------------+
                               |  Line-based stdin / stdout
                               v
+-------------------------------------------------------------+
|                 Compiled C Scheduling Engine                |
|                    (c_engine/scheduler.exe)                 |
|  - 2D Adjacency Matrix (graph[20][20])                      |
|  - Greedy Graph Coloring in C11                             |
|  - Strict boundary, integer, and self-conflict validation   |
+-------------------------------------------------------------+
```

---

## 5. C Engine Standard I/O Protocol Contract

The standalone C executable communicates non-interactively via standard input (`stdin`) and standard output (`stdout`).

### Standard Input Format (`stdin`)
```
N
E
a1 b1
a2 b2
...
```
- **Line 1:** Number of subjects $N$ ($1 \le N \le 20$).
- **Line 2:** Number of conflicts $E$ ($0 \le E \le \frac{N(N - 1)}{2}$).
- **Lines 3 to $E + 2$:** Two space-separated 1-based subject indices representing a conflict.

#### Example Input:
```
5
4
1 2
1 3
2 3
3 4
```

### Standard Output Format (`stdout`)
```
K
s1
s2
...
sN
```
- **Line 1:** Total number of time slots used $K$.
- **Lines 2 to $N + 1$:** The 1-based assigned time slot for each subject in order (Subject 1 through Subject $N$).

#### Example Output:
```
3
1
2
3
1
1
```

### Diagnostics & Error Handling (`stderr`)
If any input validation fails (e.g., self-conflict, index out of range, malformed integer, premature EOF):
- The C program prints a descriptive error message to `stderr`.
- The process terminates immediately with exit code `1`.

---

## 6. Project Structure

```
university-exam-scheduler/
│
├── c_engine/
│   └── scheduler.c             # Standalone C11 graph coloring engine
│
├── backend/
│   ├── __init__.py             # Python package marker
│   ├── app.py                  # Flask REST API server and static host
│   └── requirements.txt        # Backend dependencies (Flask, Gunicorn)
│
├── frontend/
│   ├── index.html              # Academic dashboard layout
│   ├── style.css               # Clean, accessible styling
│   └── script.js               # Dynamic forms, conflict manager, API integration
│
├── tests/
│   └── test_scheduler.py       # 29 automated tests (C unit, Flask API, integration)
│
├── Dockerfile                  # Production container definition for Render
├── .dockerignore               # Build context exclusions
├── .gitignore                  # Ignores compiled binaries and python caches
└── README.md                   # Complete documentation and viva guide
```

---

## 7. Prerequisites & Environment Setup

### Prerequisites
1. **Python 3.8+** (Python 3.13 tested)
2. **GCC / MinGW-w64** (or any C11-compliant C compiler)

### Step 1: Verify Installed Tools
Open PowerShell or your terminal and run:

```powershell
python --version
gcc --version
```

If GCC is not recognized:
- Install **MinGW-w64** via MSYS2 (`pacman -S mingw-w64-ucrt-x86_64-gcc`) or download the MinGW-w64 installer.
- Ensure the `bin` directory containing `gcc.exe` is added to your system `PATH`.

---

### Step 2: Install Python Dependencies

From the project root directory:

```powershell
cd "university-exam-scheduler"

# (Optional but recommended) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Flask
pip install -r backend/requirements.txt
```

---

### Step 3: Compile the C Scheduling Engine

Compile `scheduler.c` using GCC:

#### On Windows (PowerShell / Command Prompt):
```powershell
gcc -std=c11 -Wall -Wextra -O2 c_engine/scheduler.c -o c_engine/scheduler.exe
```

#### On Linux / macOS:
```bash
gcc -std=c11 -Wall -Wextra -O2 c_engine/scheduler.c -o c_engine/scheduler
```

*(Note: If you run the Flask backend directly, it includes an auto-compilation fallback that will invoke GCC if the binary is missing).*

---

### Step 4: Run the Application

Start the Flask server:

```powershell
python backend/app.py
```

You should see output similar to:
```text
[Info] C scheduling engine ready at: .../c_engine/scheduler.exe
[Info] Starting University Examination Scheduler on http://127.0.0.1:5000 ...
 * Running on http://127.0.0.1:5000
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Stopping the Server
Press `Ctrl + C` in the terminal to cleanly terminate the Flask server.

---

## 8. Docker Build & Run Instructions (Local)

The application includes a production-grade `Dockerfile` using `python:3.11-slim`, which installs GCC, compiles `c_engine/scheduler.c` natively into a Linux binary (`c_engine/scheduler`), and serves the application via Gunicorn.

### Prerequisites for Docker:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on Windows (or Docker Engine on Linux/macOS).

### Step 1: Build the Docker Image
From the `university-exam-scheduler` project root:

```powershell
docker build -t exam-scheduler:latest .
```

### Step 2: Run the Docker Container Locally
Run the container, forwarding port 5000 to the container port (defaults to 10000):

```powershell
docker run --rm -p 5000:10000 -e PORT=10000 exam-scheduler:latest
```

Open your browser at:
```
http://localhost:5000
```

### Step 3: Run Automated Tests Inside Docker Container
To run the full 29-test automated suite inside the clean Linux container environment:

```powershell
docker run --rm exam-scheduler:latest python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 9. Free Deployment on Render using Docker

[Render](https://render.com/) supports free-tier web services deployed directly from a GitHub repository using Docker.

### Step-by-Step Deployment Guide:

1. **Push your project to GitHub:**
   ```powershell
   git init
   git add .
   git commit -m "Initial commit of University Exam Scheduler with Dockerfile"
   git branch -M main
   git remote add origin https://github.com/<your-username>/university-exam-scheduler.git
   git push -u origin main
   ```

2. **Create a Free Account on Render:**
   - Go to [render.com](https://render.com/) and sign in with your GitHub account.

3. **Create a New Web Service:**
   - On the Render Dashboard, click **New +** and select **Web Service**.
   - Choose **Build and deploy from a Git repository** and connect your `university-exam-scheduler` repository.

4. **Configure Service Settings:**
   - **Name:** `university-exam-scheduler` (or your choice)
   - **Region:** Closest region (e.g., Oregon, Frankfurt, Singapore)
   - **Branch:** `main`
   - **Language / Runtime:** Select **Docker** (Render will automatically detect the `Dockerfile` at the root).
   - **Instance Type:** Select **Free** (0.1 CPU, 512 MB RAM).

5. **Deploy:**
   - Click **Deploy Web Service**.
   - Render will automatically:
     1. Build the Docker image from `Dockerfile`.
     2. Install GCC and compile `c_engine/scheduler.c`.
     3. Install Flask and Gunicorn from `backend/requirements.txt`.
     4. Set the `PORT` environment variable (usually `10000`).
     5. Start Gunicorn with `exec gunicorn --bind 0.0.0.0:${PORT} ...`.
   - Once the deployment log displays `Your service is live at https://<your-app>.onrender.com`, open the URL to view your live application!

---

## 10. API Specification

### Endpoint: `POST /api/schedule`

#### Request Headers:
`Content-Type: application/json`

#### Request Body (JSON):
```json
{
  "subjects": [
    "Mathematics",
    "Physics",
    "Programming",
    "Chemistry"
  ],
  "conflicts": [
    [0, 1],
    [0, 2],
    [1, 2],
    [2, 3]
  ]
}
```
*Note: Conflict pairs use 0-based indices corresponding to the positions in `subjects`.*

#### Successful Response (`200 OK`):
```json
{
  "success": true,
  "total_slots": 3,
  "schedule": [
    {
      "subject": "Mathematics",
      "slot": 1
    },
    {
      "subject": "Physics",
      "slot": 2
    },
    {
      "subject": "Programming",
      "slot": 3
    },
    {
      "subject": "Chemistry",
      "slot": 1
    }
  ],
  "slots": [
    {
      "slot": 1,
      "subjects": [
        "Mathematics",
        "Chemistry"
      ]
    },
    {
      "slot": 2,
      "subjects": [
        "Physics"
      ]
    },
    {
      "slot": 3,
      "subjects": [
        "Programming"
      ]
    }
  ]
}
```

#### Error Response (`400 Bad Request` or `500 Internal Server Error`):
```json
{
  "success": false,
  "error": "A subject cannot conflict with itself."
}
```

---

## 11. Running Automated Tests

A comprehensive suite of **29 unit and integration tests** is provided in `tests/test_scheduler.py`.

Run the test suite using Python's standard `unittest` discovery:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### What is Tested:
1. **C Engine Direct Tests:**
   - Single subject with 0 conflicts.
   - Multiple subjects with 0 conflicts.
   - 2 conflicting subjects (requires 2 slots).
   - Complete graph $K_3$ (requires 3 distinct slots).
   - Even cycle $C_4$ (sharing slots).
   - Disconnected graphs and isolated vertices.
   - Linear chain graph $P_4$.
   - Boundary test with maximum 20 subjects.
   - Out-of-bounds subjects ($0$, $21$, negative).
   - Out-of-bounds conflict indices.
   - Self-conflicts ($u = v$).
   - Truncated and malformed inputs.
2. **Backend API Validation Tests:**
   - Valid requests.
   - Non-JSON payload handling.
   - Missing required keys.
   - Empty lists and empty subject strings.
   - Duplicate subject names.
   - Non-integer or boolean conflict indices.
   - Duplicate conflict pairs.
   - Missing C binary and timeout simulations.
   - Malformed C stdout handling.
3. **Frontend Asset Serving Tests:**
   - `GET /` (`index.html`)
   - `GET /style.css`
   - `GET /script.js`
4. **End-to-End Integration Tests:**
   - Full round-trip verifying that the returned timetable is conflict-free for a real university exam dataset.

---

## 12. Frequently Asked Questions (DSA Viva Prep)

**Q1: Why is graph coloring suitable for timetable scheduling?**  
> Graph coloring naturally maps conflicting events to vertices connected by edges. Assigning colors to vertices such that no adjacent vertices share a color guarantees that no two conflicting exams are scheduled simultaneously.

**Q2: What is the chromatic number of a graph?**  
> The chromatic number $\chi(G)$ is the minimum number of colors needed to color the vertices of graph $G$ such that no two adjacent vertices share the same color.

**Q3: Why use an adjacency matrix over an adjacency list for this project?**  
> For dense graphs or graphs with a fixed maximum size (here $N \le 20$), an adjacency matrix provides:
> 1. $\mathcal{O}(1)$ edge lookup time.
> 2. Zero pointer manipulation or dynamic heap allocation (`malloc`), making the C code simpler and less prone to memory leaks.
> 3. Clear educational clarity for 1st-year students learning multi-dimensional arrays.

**Q4: How does the backend communicate with C without writing temporary files?**  
> The Python Flask backend uses `subprocess.run(..., input=c_input_str, capture_output=True, shell=False)`. Data is piped directly via operating system standard streams (`stdin`/`stdout`), ensuring fast, in-memory execution.

---

## 13. Known Limitations & Future Scope

### Known Limitations
- The maximum subject limit is set to 20 to preserve visual simplicity on a single screen and adhere to standard mini project limits.
- Greedy graph coloring uses the natural input order of subjects, which may produce a slightly higher slot count than the theoretical minimum chromatic number for certain pathological graphs.

### Future Scope
- **Welsh-Powell Ordering:** Sort vertices by descending degree prior to coloring to achieve closer-to-optimal colorings.
- **Room Capacity & Invigilator Constraints:** Extend the graph model to bipartite matching for room and faculty assignment.
- **Student Enrollment Import:** Allow uploading CSV files of student course registrations to automatically construct the conflict graph.

