"""Starter checks exercise basic setup. They are not complete acceptance coverage."""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting, importing


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'demo.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_seed_is_repeatable(self):
        storage.seed(self.db)
        self.assertEqual(len(reporting.invoices(self.db)), 6)

    def test_seed_summary(self):
        summary = reporting.overview(self.db)['summary']
        self.assertEqual(summary['invoice_count'], 6)
        self.assertEqual(summary['outstanding'], 3209.99)

    def test_one_valid_invoice(self):
        result = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,SMOKE-1,25.00,2026-09-09\n',
            'invoices'
        )
        self.assertEqual(result['imported'], 1)

    def test_mixed_invoice_import_keeps_valid_rows(self):
        csv_text = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,TEST-VALID-1,84.00,2026-09-12\n'
            'NORTH,TEST-INVALID,not-a-number,2026-09-12\n'
            'MAPLE,TEST-VALID-2,100.00,2026-09-13\n'
        )

        result = importing.import_csv(self.db, csv_text, 'invoices')

        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(result['errors'][0]['line'], 3)

    def test_payment_matches_customer_and_invoice_not_amount(self):
        csv_text = (
            'payment_id,customer_id,invoice_number,amount\n'
            'TEST-P1,MAPLE,INV-200,1250.00\n'
        )

        result = importing.import_csv(self.db, csv_text, 'payments')

        self.assertEqual(result['imported'], 1)

        harbor = next(
            r for r in reporting.invoices(self.db)
            if r['invoice_number'] == 'INV-100'
        )
        maple = next(
            r for r in reporting.invoices(self.db)
            if r['invoice_number'] == 'INV-200'
        )

        self.assertEqual(harbor['paid'], 0)
        self.assertEqual(maple['paid'], 1250.00)

    def test_export_preserves_cents(self):
        csv_text = (
            'customer_id,invoice_number,amount,due_date\n'
            'NORTH,TEST-MONEY-1,19.99,2026-09-12\n'
        )

        importing.import_csv(self.db, csv_text, 'invoices')

        exported = reporting.export_csv(self.db)

        self.assertIn(
            'NORTH,TEST-MONEY-1,19.99,0.00,19.99,open',
            exported
        )

    def test_invoice_duplicate_and_conflict(self):
        csv_text = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,TEST-DUP-1,80.00,2026-09-10\n'
        )

        first = importing.import_csv(self.db, csv_text, 'invoices')
        self.assertEqual(first['imported'], 1)

        duplicate = importing.import_csv(self.db, csv_text, 'invoices')
        self.assertEqual(duplicate['skipped'], 1)

        conflict_csv = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,TEST-DUP-1,90.00,2026-09-10\n'
        )

        conflict = importing.import_csv(self.db, conflict_csv, 'invoices')

        self.assertEqual(conflict['rejected'], 1)

        invoice = next(
            r for r in reporting.invoices(self.db)
            if r['invoice_number'] == 'TEST-DUP-1'
        )

        self.assertEqual(invoice['amount'], 80.00)

    def test_invoice_status_filter_returns_requested_status(self):
        open_rows = reporting.invoices(self.db, status='open')
        paid_rows = reporting.invoices(self.db, status='paid')

        self.assertTrue(open_rows)
        self.assertTrue(paid_rows)

        self.assertTrue(
            all(row['status'] == 'open' for row in open_rows)
        )
        self.assertTrue(
            all(row['status'] == 'paid' for row in paid_rows)
        )

        self.assertNotIn(
            'INV-101',
            [row['invoice_number'] for row in open_rows]
        )
        self.assertIn(
            'INV-101',
            [row['invoice_number'] for row in paid_rows]
        )

    def test_payment_reference_when_amount_is_unique(self):
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\n'
            'SMOKE-P1,HARBOR,INV-100,20.00\n',
            'payments'
        )
        self.assertEqual(result['imported'], 1)

        invoice = next(
            r for r in reporting.invoices(self.db)
            if r['invoice_number'] == 'INV-100'
        )
        self.assertEqual(invoice['paid'], 20.00)

    def test_export_has_header(self):
        self.assertTrue(
            reporting.export_csv(self.db).startswith(
                'customer_id,invoice_number,amount,paid,balance,status'
            )
        )


if __name__ == '__main__':
    unittest.main()