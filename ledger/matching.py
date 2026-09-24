from .storage import invoice_by_key


def find_invoice(db, payment):
    '''
    candidates = db.execute('SELECT * FROM invoices ORDER BY id').fetchall()
    amount_match = next((r for r in candidates if r['amount'] == payment['amount']), None)
    
    # They make amount the first matching criterion.(Above 2 lines)
    '''
    exact = invoice_by_key(db, payment['customer_id'], payment['invoice_number'])
    return exact['id'] if exact else None
    #replaced by above 2 lines
    if amount_match is not None:
        return amount_match['id']
    exact = invoice_by_key(db, payment['customer_id'], payment['invoice_number'])
    return exact['id'] if exact else None
