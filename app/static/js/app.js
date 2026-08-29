// Frontend Application Logic
document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const jobForm = document.getElementById("jobForm");
    const editingJobId = document.getElementById("editingJobId");
    const btnSubmitJob = document.getElementById("btnSubmitJob");
    const btnCancelEdit = document.getElementById("btnCancelEdit");
    const jobFormHeaderTitle = document.getElementById("jobFormHeaderTitle");
    const searchJobsInput = document.getElementById("searchJobsInput");

    const selectJobFilter = document.getElementById("selectJobFilter");
    const dropZone = document.getElementById("dropZone");
    const resumeFileInput = document.getElementById("resumeFileInput");
    const fileListDisplay = document.getElementById("fileListDisplay");
    const btnUploadScreen = document.getElementById("btnUploadScreen");
    const btnRescreen = document.getElementById("btnRescreen");
    const resultsTableBody = document.getElementById("resultsTableBody");
    const searchCandidatesInput = document.getElementById("searchCandidatesInput");

    // Bulk selection elements
    const selectAllCheckbox = document.getElementById("selectAllCheckbox");
    const bulkActionBar = document.getElementById("bulkActionBar");
    const selectedCountBadge = document.getElementById("selectedCountBadge");
    const btnBulkDelete = document.getElementById("btnBulkDelete");
    
    // Modal Elements
    const candidateModal = document.getElementById("candidateModal");
    const modalCloseBtn = document.getElementById("modalCloseBtn");
    const modalBody = document.getElementById("modalBody");

    let selectedFiles = [];
    let currentResults = [];
    let selectedCandidateIds = new Set();
    let candidateSearchQuery = "";

    // 1. Job Requirements Live Search Handler
    if (searchJobsInput) {
        searchJobsInput.addEventListener("input", (e) => {
            const query = e.target.value.trim().toLowerCase();
            const jobRows = document.querySelectorAll(".job-row-item");
            
            jobRows.forEach(row => {
                const title = row.getAttribute("data-title") || "";
                const dept = row.getAttribute("data-dept") || "";
                const skills = row.getAttribute("data-skills") || "";

                if (!query || title.includes(query) || dept.includes(query) || skills.includes(query)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // 2. Candidate Live Search Handler
    if (searchCandidatesInput) {
        searchCandidatesInput.addEventListener("input", (e) => {
            candidateSearchQuery = e.target.value.trim().toLowerCase();
            renderCandidateTable();
        });
    }

    // Top Navigation Tab Switcher
    window.switchTopTab = function(tab) {
        const navTabJobs = document.getElementById("navTabJobs");
        const navTabUpload = document.getElementById("navTabUpload");
        const sectionJobs = document.getElementById("sectionJobRequirements");
        const sectionUpload = document.getElementById("sectionUploadResume");

        if (tab === 'jobs') {
            navTabJobs.classList.add("active");
            navTabUpload.classList.remove("active");
            sectionJobs.style.display = "block";
            sectionUpload.style.display = "none";
        } else {
            navTabUpload.classList.add("active");
            navTabJobs.classList.remove("active");
            sectionUpload.style.display = "block";
            sectionJobs.style.display = "none";
            
            // Auto load results if job filter is selected
            if (selectJobFilter && selectJobFilter.value) {
                loadScreeningResults(selectJobFilter.value);
            }
        }
    };

    // Edit Job from Table Action Button
    window.editJobFromList = async function(jobId) {
        switchTopTab('jobs');
        try {
            const res = await fetch(`/api/jobs/${jobId}`);
            if (!res.ok) throw new Error("Failed to fetch job details");
            const job = await res.json();

            editingJobId.value = job.id;
            document.getElementById("jobTitle").value = job.title || "";
            document.getElementById("jobDepartment").value = job.department || "";
            document.getElementById("requiredSkills").value = (job.required_skills || []).join(", ");
            document.getElementById("preferredSkills").value = (job.preferred_skills || []).join(", ");
            document.getElementById("minExp").value = job.min_experience_years || 0;
            document.getElementById("jobDescription").value = job.description || "";

            if (jobFormHeaderTitle) jobFormHeaderTitle.innerText = `Edit Job Requirement (ID: ${job.id})`;
            if (btnSubmitJob) btnSubmitJob.innerText = `Update Requirement (ID: ${job.id})`;
            if (btnCancelEdit) btnCancelEdit.style.display = "inline-flex";

            // Scroll form into view smoothly
            jobForm.scrollIntoView({ behavior: 'smooth' });
        } catch (err) {
            alert("Error loading job details: " + err.message);
        }
    };

    // Reset Job Form to Create Mode
    window.resetJobForm = function() {
        if (editingJobId) editingJobId.value = "";
        if (jobForm) jobForm.reset();
        if (jobFormHeaderTitle) jobFormHeaderTitle.innerText = "Create Job Requirement";
        if (btnSubmitJob) btnSubmitJob.innerText = "Create Job Requirement";
        if (btnCancelEdit) btnCancelEdit.style.display = "none";
    };

    // Delete Job from Table Action Button
    window.deleteJobFromList = async function(jobId, jobTitle) {
        if (!confirm(`Are you sure you want to delete Job Requirement "${jobTitle}" (ID: ${jobId})? This will remove its associated screening records.`)) return;

        try {
            const res = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Failed to delete job");
            alert(`Job Requirement "${jobTitle}" deleted successfully!`);
            window.location.reload();
        } catch (err) {
            alert("Error deleting job: " + err.message);
        }
    };

    // Create / Update Job Form Submit
    if (jobForm) {
        jobForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const jobId = editingJobId ? editingJobId.value : "";
            const title = document.getElementById("jobTitle").value.trim();
            const department = document.getElementById("jobDepartment").value.trim();
            const reqSkills = document.getElementById("requiredSkills").value.split(",").map(s => s.trim()).filter(Boolean);
            const prefSkills = document.getElementById("preferredSkills").value.split(",").map(s => s.trim()).filter(Boolean);
            const minExp = parseInt(document.getElementById("minExp").value, 10) || 0;
            const description = document.getElementById("jobDescription").value.trim();

            if (!title || !description || reqSkills.length === 0) {
                alert("Please fill in Job Title, Required Skills, and Job Description.");
                return;
            }

            const payload = {
                title: title,
                department: department,
                required_skills: reqSkills,
                preferred_skills: prefSkills,
                min_experience_years: minExp,
                description: description
            };

            btnSubmitJob.disabled = true;
            btnSubmitJob.innerText = jobId ? "Updating Requirement..." : "Creating Requirement...";

            try {
                let res;
                if (jobId) {
                    // PUT update
                    res = await fetch(`/api/jobs/${jobId}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                } else {
                    // POST create
                    res = await fetch("/api/jobs/", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                }

                if (!res.ok) throw new Error("Failed to save job requirement");

                const savedJob = await res.json();
                alert(`Job "${savedJob.title}" ${jobId ? 'updated' : 'created'} successfully!`);
                window.location.reload();
            } catch (err) {
                alert("Error saving job: " + err.message);
            } finally {
                btnSubmitJob.disabled = false;
                btnSubmitJob.innerText = jobId ? `Update Requirement (ID: ${jobId})` : "Create Job Requirement";
            }
        });
    }

    // Load initial screening results if job selected
    if (selectJobFilter && selectJobFilter.value) {
        loadScreeningResults(selectJobFilter.value);
    }

    // Job Selection Change for Results Filtering
    if (selectJobFilter) {
        selectJobFilter.addEventListener("change", (e) => {
            const jobId = e.target.value;
            selectedCandidateIds.clear();
            updateBulkActionBar();
            if (jobId) {
                loadScreeningResults(jobId);
            } else {
                resultsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 24px;">Select a Job Description above to view candidate screening results.</td></tr>`;
            }
        });
    }

    // File Drag and Drop Handling
    if (dropZone && resumeFileInput) {
        dropZone.addEventListener("click", () => resumeFileInput.click());

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                handleFileSelection(Array.from(e.dataTransfer.files));
            }
        });

        resumeFileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(Array.from(e.target.files));
            }
        });
    }

    function handleFileSelection(files) {
        selectedFiles = files;
        if (selectedFiles.length > 0) {
            fileListDisplay.innerHTML = `<div style="margin-top: 8px; font-size: 0.8rem; color: #2563eb;">Selected: ${selectedFiles.map(f => f.name).join(", ")}</div>`;
        } else {
            fileListDisplay.innerHTML = "";
        }
    }

    // Upload Resumes & Run Screening
    if (btnUploadScreen) {
        btnUploadScreen.addEventListener("click", async () => {
            const jobId = selectJobFilter ? selectJobFilter.value : null;
            if (!jobId) {
                alert("Please select or create a Job Requirement first.");
                return;
            }

            if (selectedFiles.length === 0) {
                alert("Please select at least one resume file (PDF, DOCX, TXT) to upload.");
                return;
            }

            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append("files", file);
            });

            btnUploadScreen.disabled = true;
            btnUploadScreen.innerText = "Processing Resumes...";

            try {
                // 1. Upload Resumes
                const uploadRes = await fetch("/api/candidates/upload", {
                    method: "POST",
                    body: formData
                });

                if (!uploadRes.ok) {
                    const errJson = await uploadRes.json();
                    throw new Error(errJson.detail || "Upload failed");
                }

                // 2. Trigger AI Screening against selected Job
                const screenRes = await fetch(`/api/screening/screen/${jobId}`, {
                    method: "POST"
                });

                if (!screenRes.ok) throw new Error("Screening execution failed");

                selectedFiles = [];
                resumeFileInput.value = "";
                fileListDisplay.innerHTML = "";
                
                await loadScreeningResults(jobId);
                alert("Resumes processed and candidates evaluated!");
            } catch (err) {
                alert("Error during upload & screening: " + err.message);
            } finally {
                btnUploadScreen.disabled = false;
                btnUploadScreen.innerText = "Upload & Screen";
            }
        });
    }

    // Rescreen All Candidates Button
    if (btnRescreen) {
        btnRescreen.addEventListener("click", async () => {
            const jobId = selectJobFilter ? selectJobFilter.value : null;
            if (!jobId) {
                alert("Please select a Job Description to rescreen.");
                return;
            }

            btnRescreen.disabled = true;
            btnRescreen.innerText = "Evaluating...";

            try {
                const res = await fetch(`/api/screening/screen/${jobId}`, { method: "POST" });
                if (!res.ok) throw new Error("Rescreening failed");
                await loadScreeningResults(jobId);
                alert("All candidates re-evaluated successfully!");
            } catch (err) {
                alert("Error re-evaluating: " + err.message);
            } finally {
                btnRescreen.disabled = false;
                btnRescreen.innerText = "Re-evaluate All";
            }
        });
    }

    // Select All Checkbox Handler
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", (e) => {
            const isChecked = e.target.checked;
            const checkboxes = document.querySelectorAll(".cand-checkbox");
            checkboxes.forEach(cb => {
                cb.checked = isChecked;
                const candId = parseInt(cb.getAttribute("data-cand-id"), 10);
                if (isChecked) {
                    selectedCandidateIds.add(candId);
                } else {
                    selectedCandidateIds.delete(candId);
                }
            });
            updateBulkActionBar();
        });
    }

    window.toggleCandidateSelection = function(candId, checkbox) {
        if (checkbox.checked) {
            selectedCandidateIds.add(candId);
        } else {
            selectedCandidateIds.delete(candId);
        }
        updateBulkActionBar();
    };

    function updateBulkActionBar() {
        const count = selectedCandidateIds.size;
        if (selectedCountBadge) selectedCountBadge.innerText = count;
        if (bulkActionBar) {
            bulkActionBar.style.display = count > 0 ? "flex" : "none";
        }
        if (selectAllCheckbox) {
            const total = currentResults.length;
            selectAllCheckbox.checked = total > 0 && count === total;
        }
    }

    // Bulk Delete Action Button
    if (btnBulkDelete) {
        btnBulkDelete.addEventListener("click", async () => {
            const count = selectedCandidateIds.size;
            if (count === 0) return;

            if (!confirm(`Are you sure you want to delete ${count} selected candidate resume(s)?`)) return;

            btnBulkDelete.disabled = true;
            btnBulkDelete.innerText = "Deleting...";

            try {
                for (const candId of Array.from(selectedCandidateIds)) {
                    await fetch(`/api/candidates/${candId}`, { method: "DELETE" });
                }
                selectedCandidateIds.clear();
                updateBulkActionBar();
                
                const jobId = selectJobFilter ? selectJobFilter.value : null;
                if (jobId) {
                    await loadScreeningResults(jobId);
                } else {
                    window.location.reload();
                }
                alert(`${count} candidate(s) deleted successfully!`);
            } catch (err) {
                alert("Error during bulk delete: " + err.message);
            } finally {
                btnBulkDelete.disabled = false;
                btnBulkDelete.innerText = "Delete Selected";
            }
        });
    }

    // Delete Single Candidate Handler
    window.deleteCandidate = async function(candidateId, candidateName, event) {
        if (event) event.stopPropagation();
        const confirmText = candidateName ? `Delete candidate "${candidateName}" and remove their resume?` : "Delete this candidate resume?";
        if (!confirm(confirmText)) return;

        try {
            const res = await fetch(`/api/candidates/${candidateId}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Failed to delete candidate");

            selectedCandidateIds.delete(candidateId);
            updateBulkActionBar();

            if (candidateModal) candidateModal.classList.remove("active");

            const jobId = selectJobFilter ? selectJobFilter.value : null;
            if (jobId) {
                await loadScreeningResults(jobId);
            } else {
                window.location.reload();
            }
        } catch (err) {
            alert("Error deleting candidate: " + err.message);
        }
    };

    // Fetch screening results
    async function loadScreeningResults(jobId) {
        if (!resultsTableBody) return;
        resultsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 24px;">Analyzing candidate rankings...</td></tr>`;

        try {
            const res = await fetch(`/api/screening/results?job_id=${jobId}`);
            if (!res.ok) throw new Error("Failed to load results");

            currentResults = await res.json();
            renderCandidateTable();
        } catch (err) {
            resultsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #dc2626; padding: 24px;">Failed to load results: ${err.message}</td></tr>`;
        }
    }

    // Render candidate table with truncated skills & (i) info icon button
    function renderCandidateTable() {
        if (!resultsTableBody) return;
        if (!currentResults || currentResults.length === 0) {
            resultsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 24px;">No candidates evaluated for this job yet. Drop resumes in the left panel to start!</td></tr>`;
            return;
        }

        const filtered = currentResults.filter(item => {
            if (!candidateSearchQuery) return true;
            const c = item.candidate || {};
            const name = (c.name || '').toLowerCase();
            const email = (c.email || '').toLowerCase();
            const filename = (c.filename || '').toLowerCase();
            const matchedSkills = (item.matched_required_skills || []).join(' ').toLowerCase();

            return name.includes(candidateSearchQuery) || 
                   email.includes(candidateSearchQuery) || 
                   filename.includes(candidateSearchQuery) || 
                   matchedSkills.includes(candidateSearchQuery);
        });

        if (filtered.length === 0) {
            resultsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 24px;">No candidate resumes match search "${candidateSearchQuery}".</td></tr>`;
            return;
        }

        let html = "";
        filtered.forEach((item, index) => {
            const c = item.candidate || {};
            const isSelected = selectedCandidateIds.has(c.id);
            const statusClass = item.recommendation === "SHORTLIST" ? "status-shortlist" :
                                 item.recommendation === "MAYBE" ? "status-maybe" : "status-reject";

            const reqMatchedFull = (item.matched_required_skills || []).join(", ") || "None";
            const reqMatchedShort = reqMatchedFull.length > 18 ? reqMatchedFull.substring(0, 18) + "..." : reqMatchedFull;

            html += `
            <tr>
                <td style="text-align: center;">
                    <input type="checkbox" class="cand-checkbox" data-cand-id="${c.id}" ${isSelected ? 'checked' : ''} onchange="toggleCandidateSelection(${c.id}, this)" style="cursor: pointer;">
                </td>
                <td style="font-weight: 600; color: #6b7280;">#${index + 1}</td>
                <td>
                    <div style="font-weight: 600; color: #111827;">${c.name || 'Candidate'}</div>
                    <div style="font-size: 0.78rem; color: #6b7280;">${c.email || c.filename || ''}</div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-weight: 600; font-size: 0.85rem;">${item.overall_score}%</span>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${item.overall_score}%;"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="status-text ${statusClass}">${item.recommendation}</span>
                </td>
                <td class="plain-skill-text">
                    <span class="truncated-skills" title="${reqMatchedFull}">${reqMatchedShort}</span>
                </td>
                <td style="text-align: center;">
                    <div style="display: flex; gap: 4px; justify-content: center;">
                        <!-- Information (i) Line Icon Button -->
                        <button class="btn-icon" onclick="openCandidateDetail(${item.id})" title="View Details">
                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="9"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                        </button>
                        <!-- Bucket (trash) Line Icon Button -->
                        <button class="btn-icon btn-icon-danger" onclick="deleteCandidate(${c.id}, '${(c.name || '').replace(/'/g, "\\'")}', event)" title="Delete Resume">
                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                        </button>
                    </div>
                </td>
            </tr>
            `;
        });

        resultsTableBody.innerHTML = html;
        updateBulkActionBar();
    }

    // Modal Close
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener("click", () => {
            candidateModal.classList.remove("active");
        });
    }

    window.openCandidateDetail = async function(screeningId) {
        try {
            const res = await fetch(`/api/screening/results`);
            const allResults = await res.json();
            const item = allResults.find(r => r.id === screeningId);
            if (!item) return;

            const c = item.candidate || {};
            const j = item.job || {};

            const statusClass = item.recommendation === "SHORTLIST" ? "status-shortlist" :
                                 item.recommendation === "MAYBE" ? "status-maybe" : "status-reject";

            const matchedReq = (item.matched_required_skills || []).join(", ") || "None";
            const missingReq = (item.missing_required_skills || []).join(", ") || "None";

            const rawTextContent = c.raw_text ? c.raw_text.trim() : "";
            const rawSnippet = rawTextContent ? rawTextContent.substring(0, 1500) : "No text content extracted.";

            modalBody.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                    <div>
                        <h2 style="font-size: 1.2rem; font-weight: 700; color: #111827;">${c.name || 'Candidate'}</h2>
                        <p style="font-size: 0.8rem; color: #6b7280;">${c.email || 'No Email'} | ${c.phone || 'No Phone'} | File: ${c.filename || ''}</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="status-text ${statusClass}">${item.recommendation}</span>
                        <button class="btn-icon btn-icon-danger" onclick="deleteCandidate(${c.id}, '${(c.name || '').replace(/'/g, "\\'")}', event)" title="Delete Resume">
                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                        </button>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; background: #f9fafb; padding: 12px; border-radius: 6px; border: 1px solid #e5e7eb;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.72rem; color: #6b7280;">OVERALL MATCH</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #111827;">${item.overall_score}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.72rem; color: #6b7280;">SKILLS MATCH</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #111827;">${item.skills_score}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.72rem; color: #6b7280;">EXPERIENCE MATCH</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #111827;">${item.experience_score}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.72rem; color: #6b7280;">VECTOR SIMILARITY</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #111827;">${item.vector_similarity_score}%</div>
                    </div>
                </div>

                <div style="margin-bottom: 12px;">
                    <h4 style="font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">Skills Breakdown</h4>
                    <p style="font-size: 0.8rem; margin-bottom: 2px;"><strong>Matched:</strong> ${matchedReq}</p>
                    <p style="font-size: 0.8rem;"><strong>Missing:</strong> ${missingReq}</p>
                </div>

                <div style="margin-bottom: 12px;">
                    <h4 style="font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">Rationale</h4>
                    <div style="background: #f9fafb; border-left: 3px solid #6b7280; padding: 8px 10px; border-radius: 4px; font-size: 0.8rem; color: #374151;">
                        ${item.reasoning}
                    </div>
                </div>

                <div>
                    <h4 style="font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">Raw Resume Extract Snippet</h4>
                    <pre style="background: #f9fafb; padding: 10px; border-radius: 6px; font-size: 0.75rem; max-height: 160px; overflow-y: auto; color: #374151; font-family: monospace; white-space: pre-wrap; word-break: break-word; border: 1px solid #e5e7eb;">${rawSnippet}</pre>
                </div>
            `;

            candidateModal.classList.add("active");
        } catch (err) {
            alert("Error loading detail: " + err.message);
        }
    };
});
