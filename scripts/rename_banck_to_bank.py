import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from repository.database import db
import sqlalchemy as sa

"""
Script de migração simples para SQLite que renomeia a coluna
`banck_payment_id` para `bank_payment_id` recriando a tabela `payment`.
Executar: c:/Modulo_5/.venv/Scripts/python.exe scripts/rename_banck_to_bank.py
"""

with app.app_context():
    engine = db.engine
    inspector = sa.inspect(engine)
    if 'payment' not in inspector.get_table_names():
        print('Tabela `payment` não existe. Nada a fazer.')
    else:
        cols = [c['name'] for c in inspector.get_columns('payment')]
        print('Colunas atuais:', cols)
        if 'banck_payment_id' in cols and 'bank_payment_id' not in cols:
            print('Iniciando migração: renomeando banck_payment_id → bank_payment_id')
            with engine.begin() as conn:
                # Cria tabela temporária com o novo schema
                conn.execute(sa.text(
                    'CREATE TABLE payment_new ('
                    'id INTEGER PRIMARY KEY,'
                    'valor FLOAT,'
                    'pago BOOLEAN,'
                    'bank_payment_id VARCHAR(200),'
                    'qr_code VARCHAR(100),'
                    'expiration_date DATETIME'
                    ')' ))

                # Copia os dados da coluna com typo para a nova coluna
                conn.execute(sa.text(
                    'INSERT INTO payment_new (id, valor, pago, bank_payment_id, qr_code, expiration_date) '
                    'SELECT id, valor, pago, banck_payment_id, qr_code, expiration_date FROM payment;'
                ))

                # Remove tabela antiga e renomeia a nova
                conn.execute(sa.text('DROP TABLE payment;'))
                conn.execute(sa.text('ALTER TABLE payment_new RENAME TO payment;'))

            print('Migração concluída com sucesso.')
        else:
            print('Migração não necessária: coluna já está correta ou coluna com typo ausente.')
