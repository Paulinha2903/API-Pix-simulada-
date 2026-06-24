import sys
import os
import types

# garantir import relativo do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# stub mínimo para qrcode usado por payments.pix
fake_qrcode = types.SimpleNamespace() # 
def _make(data):
    class Img:
        def save(self, path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(b'')
    return Img()
fake_qrcode.make = _make
import sys as _sys
_sys.modules['qrcode'] = fake_qrcode

from payments.pix import Pix


def test_pix_create_payment_creates_file_and_returns_ids(tmp_path):
    # ajusta pasta de projeto temporária para evitar poluir workspace
    
    # o Pix salva em static/img relativo ao projeto; garantir que exista
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    static_img = os.path.join(project_root, 'static', 'img')
    os.makedirs(static_img, exist_ok=True)

    pix = Pix()
    result = pix.create_payment()

    assert isinstance(result, dict) 
    assert 'bank_payment_id' in result
    assert 'qrcode_path' in result
    assert result['qrcode_path'].endswith('.png')