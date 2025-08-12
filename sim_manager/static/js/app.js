(() => {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const toastEl = $('#toast');
  const toastBody = $('#toast-body');
  const toast = new bootstrap.Toast(toastEl, { delay: 2000 });

  function showToast(msg, ok=true) {
    toastEl.classList.remove('text-bg-primary','text-bg-danger');
    toastEl.classList.add(ok ? 'text-bg-primary' : 'text-bg-danger');
    toastBody.textContent = msg;
    toast.show();
  }

  async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  }

  async function loadHealth() {
    try {
      const data = await fetchJSON('/health');
      $('#health-text').textContent = `ok=${data.ok} | clients=${data.clients} | scheme=${data.scheme} | base_port=${data.base_port}`;
    } catch (e) {
      $('#health-text').textContent = 'ERR';
    }
  }

  function renderClients(rows) {
    const tbody = $('#clients-table tbody');
    tbody.innerHTML = '';
    rows.forEach((r) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="fw-semibold">${r.cp_id}</td>
        <td><code>${r.pid}</code></td>
        <td>${r.city ?? ''}</td>
        <td><a class="btn btn-sm btn-outline-primary" href="${r.ui}" target="_blank">Aç</a></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-danger kill-btn" data-cp="${r.cp_id}">Kill</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    $$('.kill-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const cp = btn.dataset.cp;
        try {
          await fetchJSON(`/clients/kill/${encodeURIComponent(cp)}`, { method: 'POST' });
          showToast(`Killed ${cp}`);
          await refresh();
        } catch (e) {
          showToast(`Kill failed: ${e.message}`, false);
        }
      });
    });
  }

  async function loadClients() {
    try {
      const data = await fetchJSON('/clients');
      renderClients(data);
    } catch (e) {
      renderClients([]);
    }
  }

  async function refresh() {
    await Promise.all([loadHealth(), loadClients()]);
  }

  // Form submit
  $('#spawn-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const server_url = $('#server_url').value.trim();
    const base_port  = parseInt($('#base_port').value, 10) || 8101;
    const city       = $('#city').value.trim() || null;
    const ui         = $('#ui').checked;

    const idsTabActive = $('#pane-ids').classList.contains('active');

    let body = {
      server_url,
      base_port,
      city,
      ui
    };

    if (idsTabActive) {
      const lines = $('#ids').value.split('\n').map(s => s.trim()).filter(Boolean);
      if (!lines.length) return showToast('ID listesi boş!', false);
      body.ids = lines;
    } else {
      const prefix = $('#prefix').value.trim();
      const count  = parseInt($('#count').value, 10) || 0;
      const start_index = parseInt($('#start_index').value, 10) || 1;
      if (!prefix || count < 1) return showToast('Prefix & Count zorunlu', false);
      body.prefix = prefix;
      body.count = count;
      body.start_index = start_index;
    }

    try {
      const res = await fetchJSON('/clients/spawn', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      });
      if (!res.length) showToast('Yeni client üretilmedi (muhtemelen çakışan ID).', false);
      else showToast(`Spawn OK (${res.length})`);
      await refresh();
    } catch (e) {
      showToast(`Spawn failed: ${e.message}`, false);
    }
  });

  // Buttons
  $('#refresh-btn').addEventListener('click', refresh);
  $('#kill-all-btn').addEventListener('click', async () => {
    try {
      await fetchJSON('/clients/kill-all', { method: 'POST' });
      showToast('Kill All OK');
      await refresh();
    } catch (e) {
      showToast(`Kill All failed: ${e.message}`, false);
    }
  });

  // Auto refresh
  refresh();
  setInterval(refresh, 2000);
})();
