# Handover

* Name: Nitya Gupta
* Email used for this application: [nityagupta453@gmail.com](mailto:nityagupta453@gmail.com)
* Chosen track: TRACK A
* Why this track (one or two sentences): I enjoy building software and investigating how application behaviour maps to business rules.
* Approximate total time, including setup and handover: 3hr 55 min

## Run and verify

Prerequisite: Python 3.10+ and a browser. No third-party Python dependencies are required.

Start the application:
python3 app.py --port 8790

Open http://127.0.0.1:8790.

Run regression tests:
python3 -m unittest discover -s tests -v

Final result: 10 tests ran and all passed (OK).

To restore the supplied register with the server stopped:
python3 restore_fixture.py --replace

The supplied fixture was restored before final verification. No credentials or additional dependencies are required.

## What I delivered

I investigated and repaired issues affecting import reliability, payment matching, invoice identity, reporting, money export, invoice filtering and browser feedback.

* Mixed CSV imports now reject invalid rows while continuing to process valid rows.
* Payments match using both customer_id and invoice_number; amount alone is not used.
* Invoice identity is enforced using (customer_id, invoice_number). Identical re-imports are skipped and conflicting details are rejected without replacing the original.
* Open/paid invoice filtering now returns the requested status.
* CSV export preserves currency values such as 19.99.
* Browser import feedback now reports actual imported/skipped/rejected counts and rejected CSV lines, and failed HTTP requests are shown as failures.

Regression coverage was added for these behaviours in tests/test_smoke.py.

## Evidence and limits

Failing-before/passing-after reproduction: the mixed invoice CSV originally caused an invalid row to prevent valid rows from being processed. After the fix, the same input produced 2 valid rows processed and 1 invalid row rejected with its CSV line and reason.

A separate changed-input case tested an invoice amount of 19.99. The previous export logic produced 19.98; after the fix, the exported amount and balance preserve 19.99.

The open/paid filter was reproduced against the supplied register and corrected; the open view now returns only invoices whose computed status is open.

The supplied register was restored and checked: 9 invoices, 5 payments, 7 open invoices, ₹3,698.19 outstanding, and the unmatched KEEP-U1 payment remained intact. New invoices INV-102 and INV-202 and new payments were then imported successfully and remained present after restarting. The amount-based payment mismatch was also verified: MAPLE / INV-200 received ₹1,250 while HARBOR / INV-100 remained unpaid.

I did not attempt every seeded defect. In a real project, I would investigate concurrent imports, malformed CSV edge cases, and consistency between API, browser and export views. Next I would expand end-to-end coverage.

## Tools and judgment

* ChatGPT (GPT-5.6 Luna) suggested investigation, implementation and regression-test approaches. I verified the suggestions against the application and retained changes based on observed behaviour.
* I used terminal commands, browser checks and API responses to reproduce and verify behaviour rather than relying only on automated tests.
* I used BUSINESS_RULES.md, the supplied fixture and existing tests as the source of truth. No external code was copied into the project.
