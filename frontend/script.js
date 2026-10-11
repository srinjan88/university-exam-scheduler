/**
 * University Examination Scheduler
 * Frontend Client-Side Application Logic (Vanilla JavaScript)
 *
 * Communicates with the Flask backend API (/api/schedule) which invokes
 * the standalone compiled C greedy graph coloring engine.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const numSubjectsInput = document.getElementById("num-subjects-input");
  const subjectsContainer = document.getElementById("subjects-container");
  const selectSubjectA = document.getElementById("select-subject-a");
  const selectSubjectB = document.getElementById("select-subject-b");
  const btnAddConflict = document.getElementById("btn-add-conflict");
  const conflictsList = document.getElementById("conflicts-list");
  const conflictsCount = document.getElementById("conflicts-count");
  const btnClearConflicts = document.getElementById("btn-clear-conflicts");
  const btnGenerate = document.getElementById("btn-generate");
  const btnReset = document.getElementById("btn-reset");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const statusBox = document.getElementById("status-box");
  const resultsCard = document.getElementById("results-card");
  const totalSlotsBadge = document.getElementById("total-slots-badge");
  const timetableTbody = document.getElementById("timetable-tbody");
  const slotsContainer = document.getElementById("slots-container");

  // Application State
  const defaultSubjects = [
    "Data Structures",
    "Operating Systems",
    "Discrete Mathematics",
    "Computer Networks",
    "Database Systems"
  ];

  let state = {
    subjectCount: 5,
    subjectNames: [...defaultSubjects],
    // Array of [u, v] where u < v are 0-based indices
    conflicts: [
      [0, 1], // Data Structures & Operating Systems
      [0, 2], // Data Structures & Discrete Math
      [1, 2], // Operating Systems & Discrete Math
      [2, 3], // Discrete Math & Computer Networks
      [3, 4]  // Computer Networks & Database Systems
    ]
  };

  /**
   * Initializes the UI with the initial state.
   */
  function init() {
    renderSubjectInputs();
    updateDropdowns();
    renderConflictsList();
    attachEventListeners();
  }

  /**
   * Attaches event listeners to interactive components.
   */
  function attachEventListeners() {
    numSubjectsInput.addEventListener("change", handleSubjectCountChange);
    btnAddConflict.addEventListener("click", handleAddConflict);
    btnClearConflicts.addEventListener("click", handleClearAllConflicts);
    btnGenerate.addEventListener("click", handleGenerateTimetable);
    btnReset.addEventListener("click", handleReset);
    btnLoadSample.addEventListener("click", handleLoadSample);
  }

  /**
   * Handles changes to the number of subjects input.
   */
  function handleSubjectCountChange() {
    let newCount = parseInt(numSubjectsInput.value, 10);
    if (isNaN(newCount)) newCount = 1;
    if (newCount < 1) newCount = 1;
    if (newCount > 20) newCount = 20;
    numSubjectsInput.value = newCount;

    const oldCount = state.subjectCount;
    state.subjectCount = newCount;

    // Adjust subject names array
    if (newCount > oldCount) {
      for (let i = oldCount; i < newCount; i++) {
        state.subjectNames.push(`Subject ${i + 1}`);
      }
    } else if (newCount < oldCount) {
      state.subjectNames = state.subjectNames.slice(0, newCount);
      // Prune conflicts involving removed subjects
      state.conflicts = state.conflicts.filter(
        ([u, v]) => u < newCount && v < newCount
      );
    }

    renderSubjectInputs();
    updateDropdowns();
    renderConflictsList();
  }

  /**
   * Renders the subject name input fields.
   */
  function renderSubjectInputs() {
    subjectsContainer.innerHTML = "";

    state.subjectNames.forEach((name, index) => {
      const itemDiv = document.createElement("div");
      itemDiv.className = "subject-item";

      const label = document.createElement("label");
      label.setAttribute("for", `subject-input-${index}`);
      label.textContent = `Subject ${index + 1}`;

      const input = document.createElement("input");
      input.type = "text";
      input.id = `subject-input-${index}`;
      input.className = "form-control";
      input.value = name;
      input.maxLength = 80;
      input.dataset.index = index;

      input.addEventListener("input", (e) => {
        const idx = parseInt(e.target.dataset.index, 10);
        state.subjectNames[idx] = e.target.value;
        updateDropdowns();
        renderConflictsList();
      });

      itemDiv.appendChild(label);
      itemDiv.appendChild(input);
      subjectsContainer.appendChild(itemDiv);
    });
  }

  /**
   * Updates the dropdown options with the current subject names.
   */
  function updateDropdowns() {
    const prevA = parseInt(selectSubjectA.value, 10);
    const prevB = parseInt(selectSubjectB.value, 10);

    selectSubjectA.innerHTML = "";
    selectSubjectB.innerHTML = "";

    state.subjectNames.forEach((name, index) => {
      const displayName = name.trim() || `Subject ${index + 1}`;

      const optA = document.createElement("option");
      optA.value = index;
      optA.textContent = `${index + 1}. ${displayName}`;

      const optB = document.createElement("option");
      optB.value = index;
      optB.textContent = `${index + 1}. ${displayName}`;

      selectSubjectA.appendChild(optA);
      selectSubjectB.appendChild(optB);
    });

    // Restore selected values if valid, else pick sensible defaults
    if (!isNaN(prevA) && prevA < state.subjectCount) {
      selectSubjectA.value = prevA;
    } else {
      selectSubjectA.value = 0;
    }

    if (!isNaN(prevB) && prevB < state.subjectCount) {
      selectSubjectB.value = prevB;
    } else {
      selectSubjectB.value = Math.min(1, state.subjectCount - 1);
    }
  }

  /**
   * Handles adding a new conflict pair from dropdown selections.
   */
  function handleAddConflict() {
    hideStatus();
    const idxA = parseInt(selectSubjectA.value, 10);
    const idxB = parseInt(selectSubjectB.value, 10);

    if (isNaN(idxA) || isNaN(idxB)) {
      showStatus("Please select two valid subjects.", "error");
      return;
    }

    if (idxA === idxB) {
      showStatus("A subject cannot conflict with itself. Please select two distinct subjects.", "error");
      return;
    }

    const u = Math.min(idxA, idxB);
    const v = Math.max(idxA, idxB);

    // Check for duplicate conflict
    const alreadyExists = state.conflicts.some(([cu, cv]) => cu === u && cv === v);
    if (alreadyExists) {
      const nameA = state.subjectNames[u] || `Subject ${u + 1}`;
      const nameB = state.subjectNames[v] || `Subject ${v + 1}`;
      showStatus(`Conflict between "${nameA}" and "${nameB}" already exists.`, "error");
      return;
    }

    state.conflicts.push([u, v]);
    renderConflictsList();
    showStatus("Conflict added successfully.", "success", 2000);
  }

  /**
   * Renders the badges for all currently active conflicts.
   */
  function renderConflictsList() {
    conflictsList.innerHTML = "";
    const count = state.conflicts.length;
    conflictsCount.textContent = `Current Conflicts: ${count}`;

    if (count === 0) {
      btnClearConflicts.style.display = "none";
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No conflicts defined. All examinations can potentially run concurrently.";
      conflictsList.appendChild(empty);
      return;
    }

    btnClearConflicts.style.display = "inline";

    state.conflicts.forEach(([u, v], index) => {
      const nameA = state.subjectNames[u]?.trim() || `Subject ${u + 1}`;
      const nameB = state.subjectNames[v]?.trim() || `Subject ${v + 1}`;

      const badge = document.createElement("div");
      badge.className = "conflict-badge";

      const namesSpan = document.createElement("span");
      namesSpan.className = "conflict-names";
      namesSpan.textContent = `${nameA} ⚡ ${nameB}`;

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "conflict-remove";
      removeBtn.title = "Remove this conflict";
      removeBtn.setAttribute("aria-label", `Remove conflict between ${nameA} and ${nameB}`);
      removeBtn.innerHTML = "&times;";

      removeBtn.addEventListener("click", () => {
        state.conflicts.splice(index, 1);
        renderConflictsList();
      });

      badge.appendChild(namesSpan);
      badge.appendChild(removeBtn);
      conflictsList.appendChild(badge);
    });
  }

  /**
   * Clears all conflicts.
   */
  function handleClearAllConflicts() {
    state.conflicts = [];
    renderConflictsList();
    showStatus("All conflicts removed.", "success", 2000);
  }

  /**
   * Resets the entire form to default sample values.
   */
  function handleReset() {
    state.subjectCount = 5;
    numSubjectsInput.value = 5;
    state.subjectNames = [
      "Subject 1",
      "Subject 2",
      "Subject 3",
      "Subject 4",
      "Subject 5"
    ];
    state.conflicts = [];
    hideStatus();
    resultsCard.style.display = "none";
    renderSubjectInputs();
    updateDropdowns();
    renderConflictsList();
  }

  /**
   * Loads the standard 5-subject benchmark dataset.
   */
  function handleLoadSample() {
    state.subjectCount = 5;
    numSubjectsInput.value = 5;
    state.subjectNames = [...defaultSubjects];
    state.conflicts = [
      [0, 1], // Data Structures & Operating Systems
      [0, 2], // Data Structures & Discrete Math
      [1, 2], // Operating Systems & Discrete Math
      [2, 3], // Discrete Math & Computer Networks
      [3, 4]  // Computer Networks & Database Systems
    ];
    hideStatus();
    renderSubjectInputs();
    updateDropdowns();
    renderConflictsList();
    showStatus("Sample academic dataset loaded. Click 'Generate Examination Timetable' to run.", "success", 3000);
  }

  /**
   * Validates inputs, invokes the Flask backend API, and renders the result.
   */
  async function handleGenerateTimetable() {
    hideStatus();
    resultsCard.style.display = "none";

    // 1. Client-side validation
    const cleanedNames = state.subjectNames.map((s) => s.trim());
    for (let i = 0; i < cleanedNames.length; i++) {
      if (!cleanedNames[i]) {
        showStatus(`Subject ${i + 1} name cannot be empty.`, "error");
        return;
      }
    }

    // Check for duplicate subject names
    const nameSet = new Set();
    for (let i = 0; i < cleanedNames.length; i++) {
      const lower = cleanedNames[i].toLowerCase();
      if (nameSet.has(lower)) {
        showStatus(`Duplicate subject name detected: "${cleanedNames[i]}". Subject names must be distinct.`, "error");
        return;
      }
      nameSet.add(lower);
    }

    // 2. Prepare payload
    const payload = {
      subjects: cleanedNames,
      conflicts: state.conflicts
    };

    // 3. UI Loading State
    btnGenerate.disabled = true;
    showStatus("Invoking C graph coloring scheduling engine...", "loading");

    try {
      const response = await fetch("/api/schedule", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        const errorMsg = data.error || `Server returned error status ${response.status}.`;
        showStatus(errorMsg, "error");
        btnGenerate.disabled = false;
        return;
      }

      // 4. Render successful timetable results
      renderResults(data);
      showStatus("Timetable successfully generated conflict-free!", "success");
      resultsCard.style.display = "block";
      resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      showStatus(`Network or server connection failure: ${err.message}. Ensure backend is running.`, "error");
    } finally {
      btnGenerate.disabled = false;
    }
  }

  /**
   * Renders the schedule table and slot-grouped views.
   */
  function renderResults(data) {
    totalSlotsBadge.textContent = `Total Time Slots Required: ${data.total_slots}`;

    // 1. Render Subject-Wise Table
    timetableTbody.innerHTML = "";
    data.schedule.forEach((item, index) => {
      const row = document.createElement("tr");

      const tdIndex = document.createElement("td");
      tdIndex.textContent = index + 1;

      const tdName = document.createElement("td");
      tdName.textContent = item.subject;
      tdName.style.fontWeight = "600";

      const tdSlot = document.createElement("td");
      const slotTag = document.createElement("span");
      slotTag.className = "slot-pill";
      slotTag.textContent = `Slot ${item.slot}`;
      tdSlot.appendChild(slotTag);

      row.appendChild(tdIndex);
      row.appendChild(tdName);
      row.appendChild(tdSlot);
      timetableTbody.appendChild(row);
    });

    // 2. Render Slot-Grouped View
    slotsContainer.innerHTML = "";
    data.slots.forEach((group) => {
      const groupCard = document.createElement("div");
      groupCard.className = "slot-group-card";

      const header = document.createElement("div");
      header.className = "slot-group-header";
      header.innerHTML = `<span class="slot-pill">Slot ${group.slot}</span> <span>${group.subjects.length} Concurrent Exam${group.subjects.length > 1 ? "s" : ""}</span>`;

      const subjectsRow = document.createElement("div");
      subjectsRow.className = "slot-group-subjects";

      group.subjects.forEach((subj) => {
        const subjTag = document.createElement("span");
        subjTag.className = "subject-tag";
        subjTag.textContent = subj;
        subjectsRow.appendChild(subjTag);
      });

      groupCard.appendChild(header);
      groupCard.appendChild(subjectsRow);
      slotsContainer.appendChild(groupCard);
    });
  }

  /**
   * Displays an alert status message in the status box.
   */
  function showStatus(message, type = "error", autoHideMs = null) {
    statusBox.textContent = message;
    statusBox.className = `status-box ${type}`;
    statusBox.style.display = "block";

    if (autoHideMs) {
      setTimeout(() => {
        if (statusBox.textContent === message) {
          hideStatus();
        }
      }, autoHideMs);
    }
  }

  /**
   * Hides the status box.
   */
  function hideStatus() {
    statusBox.style.display = "none";
    statusBox.textContent = "";
    statusBox.className = "status-box";
  }

  // Start initialization
  init();
});

