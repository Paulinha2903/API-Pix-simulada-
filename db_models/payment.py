from repository.database import db

# Tabela de pagamentos:
class Payment(db.Model): 
    # id, valor, pago, banck_payment_id, qr_code, expiration_date,
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float)
    pago = db.Column(db.Boolean, default=False)
    bank_payment_id = db.Column(db.String(200), nullable=True)
    qr_code = db.Column(db.String(100), nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=True)


    def to_dict(self):
        return {
            'id': self.id,
            'valor': self.valor,
            'pago': self.pago,
            'bank_payment_id': self.bank_payment_id,
            'qr_code': self.qr_code,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }