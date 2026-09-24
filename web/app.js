const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const money = n => currency.format(n);
const text = (tag, value, className = '') => {
  const node = document.createElement(tag);
  node.textContent = value;
  node.className = className;
  return node;
};

async function refresh() {
  const status = document.querySelector('#status').value;
  const responses = await Promise.all([fetch('/api/overview'), fetch(`/api/invoices?status=${status}`)]);
  if (responses.some(r => !r.ok)) throw new Error('Could not refresh the register.');
  const [data, rows] = await Promise.all(responses.map(r => r.json()));
  document.querySelector('#invoice-count').textContent = data.summary.invoice_count;
  document.querySelector('#open-count').textContent = data.summary.open_count;
  document.querySelector('#outstanding').textContent = money(data.summary.outstanding);
  const body = document.querySelector('#invoices');
  body.replaceChildren();
  rows.forEach(r => {
    const row = document.createElement('tr');
    [r.customer_name, r.invoice_number, r.due_date].forEach(v => row.append(text('td', v)));
    [r.amount, r.paid, r.balance].forEach(v => row.append(text('td', money(v), 'number')));
    row.append(text('td', r.status));
    body.append(row);
  });

  const unmatched = document.querySelector('#unmatched');
  unmatched.replaceChildren(
    ...data.unmatched_payments.map(
      p => text(
        'li',
        `${p.payment_id} · ${p.customer_id} / ${p.invoice_number} · ${money(p.amount)}`
      )
    )
  );

  if (!data.unmatched_payments.length) {
    unmatched.append(text('li', 'No unmatched payments.'));
  }

  document.querySelector('#page-error').textContent = '';
}

async function submitImport(form) {
  const feedback = form.querySelector('.feedback');
  const button = form.querySelector('button');
  button.disabled = true;
  feedback.textContent = 'Importing…';

  try {
    const csv = await form.querySelector('input').files[0].text();

    const response = await fetch(`/api/import?kind=${form.dataset.kind}`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/csv' },
      body: csv
    });

    // fetch() does not reject for HTTP 400/500, so check the response
    // explicitly to avoid showing "Import complete" for a failed request.
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || 'Import failed.');
    }

    const result = await response.json();

    // Show actual import counts so partial imports are clear to the user.
    feedback.textContent =
      `Import complete — ${result.imported} imported, ` +
      `${result.skipped} skipped, ${result.rejected} rejected.`;

    // Show the CSV line and reason for every rejected row.
    if (result.errors.length) {
      result.errors.forEach(error => {
        feedback.append(
          document.createElement('br'),
          text('span', `Line ${error.line}: ${error.reason}`)
        );
      });
    }

    await refresh();

  } catch (error) {
    feedback.textContent = `Import failed: ${error.message}`;
  } finally {
    button.disabled = false;
  }
}

document.querySelector('#status').addEventListener(
  'change',
  () => refresh().catch(e => {
    document.querySelector('#page-error').textContent = e.message;
  })
);

document.querySelectorAll('form[data-kind]').forEach(
  form => form.addEventListener('submit', e => {
    e.preventDefault();
    submitImport(form);
  })
);

refresh().catch(e => {
  document.querySelector('#page-error').textContent = e.message;
});