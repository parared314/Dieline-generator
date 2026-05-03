/**
 * form.js — Builds parameter input controls from a ParameterSpec array.
 * Consumed by app.js.
 */
const FormBuilder = (() => {
  let _specs = [];
  let _onChange = null;

  function build(specs, onChange) {
    _specs = specs;
    _onChange = onChange;

    const form = document.getElementById('params-form');
    form.innerHTML = '';

    // Group specs by .group
    const groups = {};
    specs.forEach(s => {
      const g = s.group || 'General';
      (groups[g] = groups[g] || []).push(s);
    });

    Object.entries(groups).forEach(([groupName, groupSpecs]) => {
      const fieldset = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = groupName;
      fieldset.appendChild(legend);

      groupSpecs.forEach(spec => {
        fieldset.appendChild(_buildInput(spec));
      });

      form.appendChild(fieldset);
    });
  }

  function _buildInput(spec) {
    if (spec.type === 'bool') {
      const div = document.createElement('div');
      div.className = 'param-row checkbox-row';

      const input = document.createElement('input');
      input.type = 'checkbox';
      input.id = `param-${spec.name}`;
      input.checked = Boolean(spec.default);
      input.dataset.paramName = spec.name;
      input.addEventListener('change', _onChange);

      const label = document.createElement('label');
      label.htmlFor = input.id;
      label.textContent = spec.label;

      div.appendChild(input);
      div.appendChild(label);
      return div;
    }

    if (spec.type === 'select') {
      const div = document.createElement('div');
      div.className = 'param-row';

      const label = document.createElement('label');
      label.htmlFor = `param-${spec.name}`;
      label.textContent = spec.label;

      const select = document.createElement('select');
      select.id = `param-${spec.name}`;
      select.dataset.paramName = spec.name;
      (spec.options || []).forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt.charAt(0).toUpperCase() + opt.slice(1);
        if (opt === spec.default) option.selected = true;
        select.appendChild(option);
      });
      select.addEventListener('change', _onChange);

      div.appendChild(label);
      div.appendChild(select);
      return div;
    }

    // float / int
    const div = document.createElement('div');
    div.className = 'param-row';

    const label = document.createElement('label');
    label.htmlFor = `param-${spec.name}`;

    const labelText = document.createTextNode(spec.label.replace(/\s*\(.*\)/, ''));
    label.appendChild(labelText);

    if (spec.unit) {
      const unitSpan = document.createElement('span');
      unitSpan.className = 'unit';
      unitSpan.textContent = spec.unit;
      label.appendChild(unitSpan);
    }

    const input = document.createElement('input');
    input.type = 'number';
    input.id = `param-${spec.name}`;
    input.dataset.paramName = spec.name;
    input.value = spec.default;
    if (spec.min != null) input.min = spec.min;
    if (spec.max != null) input.max = spec.max;
    if (spec.step != null) input.step = spec.step;
    input.addEventListener('input', _onChange);

    div.appendChild(label);
    div.appendChild(input);
    return div;
  }

  function collectValues() {
    const result = {};
    document.querySelectorAll('[data-param-name]').forEach(el => {
      const name = el.dataset.paramName;
      const spec = _specs.find(s => s.name === name);
      if (!spec) return;
      if (spec.type === 'bool') {
        result[name] = el.checked;
      } else if (spec.type === 'float') {
        result[name] = parseFloat(el.value) || 0;
      } else if (spec.type === 'int') {
        result[name] = parseInt(el.value) || 0;
      } else {
        result[name] = el.value;
      }
    });
    return result;
  }

  return { build, collectValues };
})();
