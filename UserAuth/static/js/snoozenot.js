function getCsrfToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

function toggleTask(taskId) {
  fetch(`/accounts/toggle-task/${taskId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify({}),
  })
    .then(res => res.json())
    .then(data => { if (data.ok) location.reload(); });
}

function deleteTask(taskId) {
  if (!confirm('Delete this task?')) return;
  fetch(`/accounts/delete_task/${taskId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })
    .then(res => res.json())
    .then(data => { if (data.ok) location.reload(); });
}

function initSidebar() {
  const toggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!toggle || !sidebar) return;

  function close() {
    sidebar.classList.remove('open');
    overlay?.classList.remove('open');
  }

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay?.classList.toggle('open');
  });
  overlay?.addEventListener('click', close);
}

document.addEventListener('DOMContentLoaded', initSidebar);
