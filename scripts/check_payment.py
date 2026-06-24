import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from db_models.payment import Payment

with app.app_context():
    p = Payment.query.order_by(Payment.id.desc()).first()
    if p:
        print({'id': p.id, 'pago': p.pago, 'bank_payment_id': p.bank_payment_id})
    else:
        print('No payments found')
