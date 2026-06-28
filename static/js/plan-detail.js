document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  initSidebar();

  const planId = parseInt(document.body.dataset.planId);
  if (!planId) { window.location.href = '/app/plans'; return; }

  /* ── Subject → dot-color cycling ──────────────── */
  const subjectColors = {};
  let colorIdx = 0;
  function colorFor(subject) {
    if (!(subject in subjectColors)) subjectColors[subject] = colorIdx++ % 8;
    return subjectColors[subject];
  }

  /* ── Progress ring ─────────────────────────────── */
  const CIRCUMFERENCE = 326.7; // 2π × 52
  function setRing(pct) {
    const fill = document.querySelector('.ring-fill');
    if (fill) fill.style.strokeDashoffset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
    const el = document.getElementById('ring-pct');
    if (el) el.textContent = Math.round(pct) + '%';
  }

  /* ── Refresh sidebar stats ─────────────────────── */
  async function refreshProgress() {
    try {
      const p = await apiGetPlanProgress(planId);
      setRing(p.progress_percentage);
      document.getElementById('stat-total').textContent     = p.total_tasks;
      document.getElementById('stat-done').textContent      = p.completed_tasks;
      document.getElementById('stat-remaining').textContent = p.remaining_tasks;
      document.getElementById('stat-days').textContent      = p.days_until_exam;
      const summary = document.getElementById('tasks-summary');
      if (summary) summary.textContent = `${p.completed_tasks} of ${p.total_tasks} completed`;
    } catch {}
  }

  /* ── Task UI update ────────────────────────────── */
  function updateTaskUI(taskId, isCompleted) {
    const item = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!item) return;
    const btn = item.querySelector('.btn-complete');
    if (isCompleted) {
      item.classList.add('completed-item');
      btn.classList.add('done'); btn.classList.remove('undone');
      btn.innerHTML = `<i class="bi bi-check-circle-fill"></i> Done`;
      // Animate badge
      const meta = item.querySelector('.task-meta-row');
      if (meta && !meta.querySelector('.badge-green')) {
        const badge = document.createElement('span');
        badge.className = 'badge-sp badge-green fade-up';
        badge.style.fontSize = '10.5px';
        badge.innerHTML = `<i class="bi bi-check-circle-fill"></i> Completed`;
        meta.appendChild(badge);
      }
    } else {
      item.classList.remove('completed-item');
      btn.classList.remove('done'); btn.classList.add('undone');
      btn.innerHTML = `<i class="bi bi-circle"></i> Mark done`;
      const badge = item.querySelector('.badge-green');
      if (badge) badge.remove();
    }
    btn.dataset.completed = isCompleted ? '1' : '0';
  }

  /* ── Toggle task completion ────────────────────── */
  async function toggleTask(taskId, isCompleted, btn) {
    btn.disabled = true;
    try {
      const updated = isCompleted
        ? await apiIncompleteTask(taskId)
        : await apiCompleteTask(taskId);
      updateTaskUI(taskId, updated.is_completed);
      await refreshProgress();
      if (updated.is_completed) showToast('Task marked as complete', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to update task', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  /* ── Render tasks grouped by date ──────────────── */
  function renderTasks(tasks) {
    const container = document.getElementById('tasks-container');
    if (!tasks || tasks.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon"><i class="bi bi-calendar-x"></i></div>
          <div class="empty-title">No tasks generated</div>
          <div class="empty-sub">Try regenerating this plan.</div>
        </div>`;
      return;
    }

    // Group by date
    const groups = {};
    tasks.forEach(t => {
      const day = t.date.slice(0, 10);
      (groups[day] = groups[day] || []).push(t);
    });

    container.innerHTML = Object.keys(groups).sort().map(day => {
      const dayTasks = groups[day];
      const label    = formatDateShort(day + 'T12:00:00');
      const doneCount = dayTasks.filter(t => t.is_completed).length;

      const items = dayTasks.map(t => {
        const ci   = colorFor(t.subject);
        const done = t.is_completed;
        return `
        <div class="task-item ${done ? 'completed-item' : ''}" data-task-id="${t.id}">
          <div class="task-dot dot-${ci}"></div>
          <div class="task-body">
            <div class="task-subject">${t.subject}</div>
            <div class="task-desc">${t.description}</div>
            <div class="task-meta-row">
              <span class="task-dur"><i class="bi bi-clock"></i> ${t.duration_hours}h</span>
              ${done ? `<span class="badge-sp badge-green" style="font-size:10.5px"><i class="bi bi-check-circle-fill"></i> Completed</span>` : ''}
            </div>
          </div>
          <div class="task-actions">
            <button class="btn-complete ${done ? 'done' : 'undone'}"
                    data-task-id="${t.id}" data-completed="${done ? '1' : '0'}">
              <i class="bi ${done ? 'bi-check-circle-fill' : 'bi-circle'}"></i>
              ${done ? 'Done' : 'Mark done'}
            </button>
          </div>
        </div>`;
      }).join('');

      return `
      <div class="day-group">
        <div class="day-header">
          <span class="day-label">${label}</span>
          <div class="day-line"></div>
          <span style="font-size:11px;color:var(--t3);white-space:nowrap">
            ${doneCount}/${dayTasks.length} done
          </span>
        </div>
        ${items}
      </div>`;
    }).join('');

    // Attach toggle listeners
    container.querySelectorAll('.btn-complete').forEach(btn => {
      btn.addEventListener('click', () => {
        const id        = parseInt(btn.dataset.taskId);
        const completed = btn.dataset.completed === '1';
        toggleTask(id, completed, btn);
      });
    });
  }

  /* ── Regenerate (via modal) ────────────────────── */
  const confirmRegen = document.getElementById('confirm-regenerate');
  const regenModal   = bootstrap.Modal.getOrCreateInstance(
    document.getElementById('regenerateModal')
  );

  confirmRegen?.addEventListener('click', async () => {
    confirmRegen.disabled = true;
    confirmRegen.innerHTML = `<span class="spinner"></span> Regenerating…`;
    try {
      await apiRegeneratePlan(planId);
      regenModal.hide();
      showToast('Plan regenerated successfully!', 'success');
      setTimeout(() => window.location.reload(), 800);
    } catch (err) {
      regenModal.hide();
      showToast(err.message || 'Failed to regenerate plan', 'error');
      confirmRegen.disabled = false;
      confirmRegen.innerHTML = `<i class="bi bi-arrow-clockwise"></i> Yes, Regenerate`;
    }
  });

  /* ── Delete (via modal) ────────────────────────── */
  const confirmDelete = document.getElementById('confirm-delete');
  const deleteModal   = bootstrap.Modal.getOrCreateInstance(
    document.getElementById('deleteModal')
  );

  confirmDelete?.addEventListener('click', async () => {
    confirmDelete.disabled = true;
    confirmDelete.innerHTML = `<span class="spinner"></span> Deleting…`;
    try {
      await apiDeletePlan(planId);
      deleteModal.hide();
      showToast('Plan deleted', 'info');
      setTimeout(() => { window.location.href = '/app/plans'; }, 600);
    } catch (err) {
      deleteModal.hide();
      showToast(err.message || 'Failed to delete plan', 'error');
      confirmDelete.disabled = false;
      confirmDelete.innerHTML = `<i class="bi bi-trash3"></i> Delete Plan`;
    }
  });

  /* ── Load page data ────────────────────────────── */
  try {
    const [plan, progress] = await Promise.all([
      apiGetPlan(planId),
      apiGetPlanProgress(planId),
    ]);

    // Header
    document.getElementById('plan-subjects-header').innerHTML =
      plan.subjects.map(s => `<span class="subject-tag" style="font-size:13px;padding:3px 11px">${s}</span>`).join('');
    document.getElementById('plan-difficulty').innerHTML = difficultyBadge(plan.difficulty);
    document.getElementById('plan-exam-date').textContent = formatDate(plan.exam_date);
    document.getElementById('plan-hours').textContent     = plan.daily_study_hours + 'h/day';
    document.getElementById('plan-created').textContent   = formatDate(plan.created_at);

    // Sidebar stats
    document.getElementById('stat-total').textContent     = progress.total_tasks;
    document.getElementById('stat-done').textContent      = progress.completed_tasks;
    document.getElementById('stat-remaining').textContent = progress.remaining_tasks;
    document.getElementById('stat-days').textContent      = progress.days_until_exam;

    // Tasks summary
    const summaryEl = document.getElementById('tasks-summary');
    if (summaryEl) summaryEl.textContent = `${progress.completed_tasks} of ${progress.total_tasks} completed`;

    // Animate ring after small delay (so CSS transition fires)
    setTimeout(() => setRing(progress.progress_percentage), 150);

    // AI content
    const expEl  = document.getElementById('ai-explanation');
    const tipsEl = document.getElementById('ai-tips');
    if (expEl)  expEl.textContent  = plan.ai_explanation || 'No explanation provided.';
    if (tipsEl) tipsEl.textContent = plan.study_tips      || 'No tips provided.';

    // Tasks
    const sorted = [...(plan.tasks || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
    renderTasks(sorted);

  } catch (err) {
    showToast('Failed to load plan details', 'error');
    document.getElementById('tasks-container').innerHTML =
      `<div class="alert-sp error"><i class="bi bi-exclamation-circle"></i> ${err.message}</div>`;
  }
});
