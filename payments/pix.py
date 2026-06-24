import uuid  # Importa a biblioteca uuid para gerar identificadores únicos
import qrcode  # Importa a biblioteca qrcode para gerar códigos QR
import os


class Pix:

    def __init__(self):
        pass

    # cria pagamento na instituição financeira
    def create_payment(self):

        bank_payment_id = str(uuid.uuid4())   # Simulação de ID de pagamento retornado pelo banco

        # codigo copia e cola do banco para o cliente pagar
        hash_payment = f'hash_payment_{bank_payment_id}'  # Simulação de hash do pagamento

        # qrcode 
        img = qrcode.make(hash_payment)  # Gera o código QR a partir do hash do pagamento

        # Garante que o diretório static/img exista
        project_root = os.path.dirname(os.path.dirname(__file__))
        img_dir = os.path.join(project_root, 'static', 'img')
        os.makedirs(img_dir, exist_ok=True)

        img_filename = f'qr_code_payment_{bank_payment_id}.png'
        img_path = os.path.join(img_dir, img_filename)
        img.save(img_path)  # Salva a imagem do código QR em um arquivo

        return {"bank_payment_id": bank_payment_id, "qrcode_path": f"static/img/{img_filename}"}