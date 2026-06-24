import sys
import os
import pytest

# Garantir que o diretório do projeto esteja no path para importar `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import types

# Stub simples para o módulo `qrcode` (evita necessidade de instalar dependência em ambiente de teste)
fake_qrcode = types.SimpleNamespace()
def _make(data):
    class Img:
        def save(self, path):
            # cria um arquivo placeholder vazio
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(b'')
    return Img()
fake_qrcode.make = _make
import sys as _sys
_sys.modules['qrcode'] = fake_qrcode

# Stub para `flask_socketio` se não estiver instalado no ambiente de teste
if 'flask_socketio' not in _sys.modules:
    import types as _types
    def _make_socketio_module():
        mod = _types.SimpleNamespace()
        class SocketIO:
            def __init__(self, app, cors_allowed_origins=None):
                self.app = app
            def emit(self, *args, **kwargs):
                return None
            def on(self, event):
                def decorator(f):
                    return f
                return decorator
        mod.SocketIO = SocketIO
        return mod
    _sys.modules['flask_socketio'] = _make_socketio_module()

from app import app
from db_models.payment import Payment
from repository.database import db


@pytest.fixture
def test_app():
    # configuração para testes: banco em memória
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


def test_create_and_confirm_flow(client, test_app):
    # Criar pagamento
    resp = client.post('/payments/pix', json={'valor': 12.34})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'payment' in data
    payment = data['payment']
    bank_id = payment.get('bank_payment_id')
    payment_id = payment.get('id')
    assert bank_id is not None
    assert payment_id is not None
    assert payment.get('pago') in (False, 0)

    # Confirmar pagamento
    resp2 = client.post('/payments/pix/confirmation', json={'bank_payment_id': bank_id, 'valor': 12.34})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2.get('id') == payment_id

    # Verificar no DB que ficou marcado como pago
    with test_app.app_context():
        p = Payment.query.get(payment_id)
        assert p is not None
        assert p.pago is True


def test_confirm_with_wrong_value_returns_400(client, test_app):
    # cria pagamento
    resp = client.post('/payments/pix', json={'valor': 50.00})
    assert resp.status_code == 200
    payment = resp.get_json()['payment']
    bank_id = payment['bank_payment_id']

    # tenta confirmar com valor diferente
    resp2 = client.post('/payments/pix/confirmation', json={'bank_payment_id': bank_id, 'valor': 40.00})
    assert resp2.status_code == 400
    data = resp2.get_json()
    assert 'erro' in data


def test_confirm_nonexistent_returns_404(client):
    # confirma pagamento que não existe
    resp = client.post('/payments/pix/confirmation', json={'bank_payment_id': 'nonexistent-id', 'valor': 10.00})
    assert resp.status_code == 404
    data = resp.get_json()
    assert 'erro' in data
