/**
 * app.js — Main controller. Wires template list, form, and preview together.
 */
const App = (() => {
  let currentTemplateId = null;
  let debounceTimer = null;

  async function init() {
    Preview.init();

    let templates;
    try {
      templates = await fetch('/api/templates').then(r => r.json());
    } catch (e) {
      Preview.showError('Could not load templates. Is the server running?');
      return;
    }

    renderTemplateList(templates);

    if (templates.length > 0) {
      selectTemplate(templates[0].id);
    }

    document.getElementById('download-btn').addEventListener('click', downloadSVG);
  }

  function renderTemplateList(templates) {
    const sidebar = document.getElementById('template-sidebar');
    sidebar.innerHTML = '<h2>Packaging Templates</h2>';

    templates.forEach(tmpl => {
      const card = document.createElement('div');
      card.className = 'template-card';
      card.dataset.id = tmpl.id;
      card.addEventListener('click', () => selectTemplate(tmpl.id));

      card.innerHTML = `
        <div class="template-thumb">
          <img src="${tmpl.thumbnail}" alt="" onerror="this.style.display='none'">
        </div>
        <div class="template-info">
          <div class="name">${tmpl.name}</div>
          <div class="desc">${tmpl.description || ''}</div>
        </div>
      `;
      sidebar.appendChild(card);
    });
  }

  async function selectTemplate(id) {
    currentTemplateId = id;

    // Update sidebar active state
    document.querySelectorAll('.template-card').forEach(card => {
      card.classList.toggle('active', card.dataset.id === id);
    });

    // Load schema
    let schema;
    try {
      schema = await fetch(`/api/templates/${id}/schema`).then(r => r.json());
    } catch (e) {
      Preview.showError('Failed to load template schema.');
      return;
    }

    // Update panel header
    const card = document.querySelector(`.template-card[data-id="${id}"]`);
    const name = card ? card.querySelector('.name').textContent : id;
    const desc = card ? card.querySelector('.desc').textContent : '';
    document.querySelector('#params-panel .panel-header h2').textContent = name;
    document.querySelector('#params-panel .panel-header p').textContent = desc;

    FormBuilder.build(schema.parameters, onParamChange);
    document.getElementById('download-btn').disabled = false;

    requestPreview();
  }

  function onParamChange() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(requestPreview, 300);
  }

  async function requestPreview() {
    if (!currentTemplateId) return;

    const params = FormBuilder.collectValues();
    Preview.showLoading();

    try {
      const resp = await fetch('/api/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: currentTemplateId, params }),
      });

      if (resp.ok) {
        const svg = await resp.text();
        Preview.render(svg);
        Preview.setStatus(`Ready — ${currentTemplateId}`);
      } else {
        const err = await resp.json();
        Preview.showError(err.detail);
      }
    } catch (e) {
      Preview.showError('Network error. Is the server running?');
    }
  }

  async function downloadSVG() {
    if (!currentTemplateId) return;
    const params = JSON.stringify(FormBuilder.collectValues());
    const url = `/api/download/${currentTemplateId}?params=${encodeURIComponent(params)}`;

    const btn = document.getElementById('download-btn');
    btn.disabled = true;
    btn.textContent = 'Generating…';

    try {
      window.location.href = url;
    } finally {
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'Download SVG';
      }, 1500);
    }
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => App.init());
