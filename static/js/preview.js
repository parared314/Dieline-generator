/**
 * preview.js — Handles SVG injection and layer visibility toggles.
 */
const Preview = (() => {
  const LAYERS = [
    { id: 'cut_lines',          label: 'Cut',   cls: 'cut'  },
    { id: 'fold_lines',         label: 'Fold',  cls: 'fold' },
    { id: 'perforation_lines',  label: 'Perf',  cls: 'perf' },
    { id: 'guides__bleed',      label: 'Guide', cls: 'guide'},
  ];

  let _container = null;
  let _statusBar = null;
  let _layerVisibility = {};

  LAYERS.forEach(l => { _layerVisibility[l.id] = true; });

  function init() {
    _container = document.getElementById('svg-container');
    _statusBar = document.getElementById('status-bar');
    _buildLayerToggles();
  }

  function _buildLayerToggles() {
    const toolbar = document.getElementById('preview-toolbar');
    const wrapper = document.createElement('div');
    wrapper.className = 'layer-toggles';

    LAYERS.forEach(layer => {
      const lbl = document.createElement('label');
      lbl.className = 'layer-toggle';

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = true;
      cb.addEventListener('change', () => {
        _layerVisibility[layer.id] = cb.checked;
        _applyLayerVisibility();
      });

      const swatch = document.createElement('span');
      swatch.className = `legend-swatch ${layer.cls}`;

      lbl.appendChild(cb);
      lbl.appendChild(swatch);
      lbl.appendChild(document.createTextNode(layer.label));
      wrapper.appendChild(lbl);
    });

    toolbar.appendChild(wrapper);
  }

  function _applyLayerVisibility() {
    const svg = _container.querySelector('svg');
    if (!svg) return;
    LAYERS.forEach(layer => {
      const g = svg.getElementById(layer.id);
      if (g) g.style.display = _layerVisibility[layer.id] ? '' : 'none';
    });
  }

  function render(svgString) {
    _container.innerHTML = svgString;
    const svg = _container.querySelector('svg');
    if (svg) {
      svg.removeAttribute('width');
      svg.removeAttribute('height');
      svg.style.width = '';
      svg.style.height = '';
      _applyLayerVisibility();
    }
    setStatus('');
  }

  function showLoading() {
    _container.innerHTML = '<div class="spinner"></div>';
    setStatus('Generating…');
  }

  function showError(detail) {
    let msg;
    if (Array.isArray(detail)) {
      msg = detail.map(e => `${e.field}: ${e.message}`).join(' | ');
    } else {
      msg = String(detail);
    }
    _container.innerHTML = `<div style="color:#e94560;font-size:0.85rem;text-align:center;padding:20px">${msg}</div>`;
    setStatus(msg, true);
  }

  function setStatus(msg, isError = false) {
    _statusBar.textContent = msg;
    _statusBar.className = isError ? 'error' : '';
  }

  return { init, render, showLoading, showError, setStatus };
})();
