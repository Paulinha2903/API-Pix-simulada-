import sys, os, json, urllib.request
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

CREATE_URL = 'http://127.0.0.1:5000/payments/pix'
CONFIRM_URL = 'http://127.0.0.1:5000/payments/pix/confirmation'

payload = {'valor': 42.42}

def post_json(url, data):
    data_bytes = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

if __name__ == '__main__':
    print('Criando pagamento...')
    create_resp = post_json(CREATE_URL, payload)
    print('Resposta criação:')
    print(json.dumps(create_resp, indent=2, ensure_ascii=False))

    bank_id = create_resp.get('payment', {}).get('bank_payment_id') or create_resp.get('payment', {}).get('bank_payment_id')
    if not bank_id:
        print('Não foi possível obter bank_payment_id da resposta.')
        sys.exit(1)

    confirm_body = {'bank_payment_id': bank_id, 'valor': payload['valor']}
    print('\nConfirmando pagamento...')
    confirm_resp = post_json(CONFIRM_URL, confirm_body)
    print('Resposta confirmação:')
    print(json.dumps(confirm_resp, indent=2, ensure_ascii=False))

    # Verifica no banco de dados (SQLite)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'payments.db')
    print('\nChecando status no DB (sqlite) em:', db_path)
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT id, valor, pago, bank_payment_id FROM payment WHERE bank_payment_id = ?', (bank_id,))
    row = cur.fetchone()
    if row:
        print({'id': row[0], 'valor': row[1], 'pago': bool(row[2]), 'bank_payment_id': row[3]})
    else:
        print('Registro não encontrado no DB.')
    conn.close()
