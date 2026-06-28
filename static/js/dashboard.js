document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  initSidebar();

  const user = getUser();
  const $ = id => document.getElementById(id);

  try {
    const [stats, plans] = await Promise.all([apiDashboard(), apiListPlans()]);

    // Personalised subtitle
    if (user?.name) {
      $('dash-subtitle').textContent = `Welcome back, ${user.name.split(' ')[0]} 👋`;
    }

    // Empty hero — show when user has no plans yet
    if (stats.total_plans === 0) {
      $('empty-hero').style.display = 'block';
    }

    // Stat cards
    $('stat-total-plans').textContent = stats.total_plans;
    $('stat-total-tasks').textContent = stats.total_tasks;
    $('stat-completed').textContent   = stats.completed_tasks;
    $('stat-remaining').textContent   = stats.remaining_tasks;

    // Overall progress bar
    const pct = stats.overall_progress_percentage;
    $('overall-pct-label').textContent          = pct.toFixed(1) + '%';
    $('overall-progress-fill').style.width      = pct + '%';

    // Streak
    $('streak-number').textContent = stats.current_streak_days;

    // Upcoming exam
    if (stats.nearest_exam_days !== null) {
      $('exam-days').textContent  = stats.nearest_exam_days;
      $('exam-label').textContent = stats.nearest_exam_days === 1 ? 'day until your exam' : 'days until your exam';
    } else {
      $('exam-days').textContent  = '—';
      $('exam-label').textContent = 'No upcoming exams';
    }

    // Recent plans list
    const listEl = $('recent-plans-list');

    if (plans.length === 0) {
      listEl.innerHTML = `
        <div style="text-align:center;padding:24px 0">
          <div style="font-size:28px;color:var(--t3);margin-bottom:8px"><i class="bi bi-journal-plus"></i></div>
          <div style="font-size:13px;color:var(--t3)">No plans yet. <a href="/app/plans" style="color:var(--cyan)">Create your first one</a>.</div>
        </div>`;
    } else {
      listEl.innerHTML = plans.slice(0, 5).map(p => {
        const subjects  = p.subjects.join(', ');
        const total     = p.tasks?.length || 0;
        const done      = p.tasks?.filter(t => t.is_completed).length || 0;
        const pct       = total > 0 ? Math.round(done / total * 100) : 0;
        const truncated = subjects.length > 42 ? subjects.slice(0, 42) + '…' : subjects;
        return `
        <div class="mini-plan-item">
          <div style="min-width:0;flex:1">
            <div class="mini-plan-name">${truncated}</div>
            <div class="mini-plan-subjects">${done}/${total} tasks · exam ${formatDate(p.exam_date)}</div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;flex-shrink:0">
            <span style="font-size:12.5px;font-weight:700;color:var(--cyan)">${pct}%</span>
            <a href="/app/plans/${p.id}" class="btn-ghost" style="padding:4px 10px;font-size:12px">Open</a>
          </div>
        </div>`;
      }).join('');
    }

  } catch (err) {
    console.error('Dashboard load error:', err);
    showToast('Failed to load dashboard data', 'error');
  }
});
