document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  initSidebar();

  /* ── State ─────────────────────────────────────────── */
  let subjects = [];
  let difficulty = 'Easy';

  /* ── Subjects tag input ────────────────────────────── */
  const tagsWrap  = document.getElementById('tags-wrap');
  const tagsInput = document.getElementById('tags-input');

  function renderTags() {
    document.querySelectorAll('.tag-pill').forEach(el => el.remove());
    subjects.forEach((s, i) => {
      const pill = document.createElement('span');
      pill.className = 'tag-pill';
      pill.innerHTML = `${s}<button type="button" data-i="${i}"><i class="bi bi-x"></i></button>`;
      pill.querySelector('button').addEventListener('click', () => {
        subjects.splice(i, 1);
        renderTags();
      });
      tagsWrap.insertBefore(pill, tagsInput);
    });
  }

  tagsInput?.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ',') && tagsInput.value.trim()) {
      e.preventDefault();
      const val = tagsInput.value.trim().replace(/,$/, '');
      if (val && !subjects.includes(val)) { subjects.push(val); renderTags(); }
      tagsInput.value = '';
    }
    if (e.key === 'Backspace' && !tagsInput.value && subjects.length) {
      subjects.pop(); renderTags();
    }
  });
  tagsWrap?.addEventListener('click', () => tagsInput?.focus());

  /* ── Difficulty picker ─────────────────────────────── */
  document.querySelectorAll('.diff-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      difficulty = btn.dataset.value;
      document.querySelectorAll('.diff-pill').forEach(b => {
        b.className = 'diff-pill';
      });
      btn.classList.add(`selected-${difficulty.toLowerCase()}`);
    });
  });
  // Default selection
  document.querySelector('[data-value="Easy"]')?.classList.add('selected-easy');

  /* ── Hours slider ──────────────────────────────────── */
  const hoursSlider = document.getElementById('hours-slider');
  const hoursValue  = document.getElementById('hours-value');
  hoursSlider?.addEventListener('input', () => {
    hoursValue.textContent = hoursSlider.value + 'h';
  });

  /* ── Load plans ────────────────────────────────────── */
  async function loadPlans() {
    const grid   = document.getElementById('plans-grid');
    const empty  = document.getElementById('empty-state');
    grid.innerHTML = '';

    try {
      const plans = await apiListPlans();

      if (plans.length === 0) {
        empty.classList.remove('hidden');
        return;
      }
      empty.classList.add('hidden');

      grid.innerHTML = plans.map(p => planCardHTML(p)).join('');

      // Attach delete buttons
      document.querySelectorAll('.btn-delete-plan').forEach(btn => {
        btn.addEventListener('click', async e => {
          e.preventDefault(); e.stopPropagation();
          if (!confirm('Delete this plan? This cannot be undone.')) return;
          btn.disabled = true;
          try {
            await apiDeletePlan(btn.dataset.id);
            loadPlans();
          } catch(err) {
            alert(err.message);
            btn.disabled = false;
          }
        });
      });

    } catch (err) {
      grid.innerHTML = `<div class="alert-sp error"><i class="bi bi-exclamation-circle"></i> ${err.message}</div>`;
    }
  }

  function planCardHTML(p) {
    const total   = p.tasks?.length || 0;
    const done    = p.tasks?.filter(t => t.is_completed).length || 0;
    const pct     = total > 0 ? Math.round(done / total * 100) : 0;
    const days    = daysUntil(p.exam_date);
    const subHTML = p.subjects.map(s => `<span class="subject-tag">${s}</span>`).join('');
    return `
    <div class="plan-card" onclick="window.location='/app/plans/${p.id}'">
      <div class="plan-card-top">
        <div class="subjects-wrap">${subHTML}</div>
        ${difficultyBadge(p.difficulty)}
      </div>
      <div class="plan-card-meta">
        <span><i class="bi bi-calendar3"></i> ${formatDate(p.exam_date)}</span>
        <span><i class="bi bi-clock"></i> ${p.daily_study_hours}h/day</span>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:5px">
          <span style="font-size:12px;color:var(--t2)">${done}/${total} tasks</span>
          <span style="font-size:12px;font-weight:700;color:var(--pri-h)">${pct}%</span>
        </div>
        <div class="progress-sp"><div class="fill" style="width:${pct}%"></div></div>
      </div>
      <div class="plan-card-footer">
        <span style="font-size:12px;color:var(--t3)">
          <i class="bi bi-hourglass-split"></i> ${days === 0 ? 'Exam today!' : days + ' days left'}
        </span>
        <div style="display:flex;gap:6px" onclick="event.stopPropagation()">
          <a href="/app/plans/${p.id}" class="btn-ghost" style="padding:5px 12px;font-size:12px">
            <i class="bi bi-eye"></i> View
          </a>
          <button class="btn-danger btn-delete-plan" data-id="${p.id}" style="padding:5px 12px;font-size:12px">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      </div>
    </div>`;
  }

  /* ── Generate Plan form submit ─────────────────────── */
  const generateForm = document.getElementById('generate-form');
  const generateBtn  = document.getElementById('btn-generate');
  const generateAlert = document.getElementById('generate-alert');

  generateForm?.addEventListener('submit', async e => {
    e.preventDefault();
    hideAlert(generateAlert);

    const examDateRaw = document.getElementById('exam-date').value;
    if (!examDateRaw) { showAlert(generateAlert, 'error', 'Please select an exam date.'); return; }
    if (subjects.length === 0) { showAlert(generateAlert, 'error', 'Add at least one subject.'); return; }

    const payload = {
      subjects,
      exam_date: examDateRaw + 'T00:00:00Z',
      daily_study_hours: parseFloat(hoursSlider.value),
      difficulty,
    };

    generateBtn.disabled = true;
    generateBtn.innerHTML = `<span class="spinner"></span> Generating…`;

    try {
      const plan = await apiGeneratePlan(payload);
      // Close modal and redirect to new plan
      const modal = bootstrap.Modal.getInstance(document.getElementById('generateModal'));
      modal?.hide();
      window.location.href = `/app/plans/${plan.id}`;
    } catch (err) {
      showAlert(generateAlert, 'error', err.message);
      generateBtn.disabled = false;
      generateBtn.innerHTML = `<i class="bi bi-stars"></i> Generate Plan`;
    }
  });

  // Reset form when modal closes
  document.getElementById('generateModal')?.addEventListener('hidden.bs.modal', () => {
    subjects = [];
    renderTags();
    difficulty = 'Easy';
    document.querySelectorAll('.diff-pill').forEach(b => b.className = 'diff-pill');
    document.querySelector('[data-value="Easy"]')?.classList.add('selected-easy');
    if (hoursSlider) { hoursSlider.value = 3; hoursValue.textContent = '3h'; }
    generateForm?.reset();
    hideAlert(generateAlert);
    generateBtn.disabled = false;
    generateBtn.innerHTML = `<i class="bi bi-stars"></i> Generate Plan`;
  });

  await loadPlans();
});
