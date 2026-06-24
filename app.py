from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for
import os
from repository.database import db
from db_models.payment import Payment
from datetime import datetime, timedelta
from payments.pix import Pix
from flask_socketio import SocketIO

# Cria a aplicação Flask
# Define o caminho de `instance` explicitamente para evitar busca automática
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
app = Flask(__name__, instance_path=instance_path)

# Configurações do banco de dados
# Aponta explicitamente para o arquivo dentro da pasta `instance` para evitar DBs duplicados
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "payments.db")}'
app.config['SECRET_KEY'] = 'SECRET_KEY_WEBSOCKET'   # Configura a chave secreta para sessões
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa o rastreamento de modificações do SQLAlchemy para melhorar o desempenho

# Inicializa o banco de dados
db.init_app(app)

# Permite conexões WebSocket de origens diferentes (útil em dev / Postman)
socketio = SocketIO(app, cors_allowed_origins="*")  # Inicializa o SocketIO para comunicação em tempo real

# Define as rotas da API
@app.route('/')
def index():
    return jsonify({"message": "Servidor rodando. Use /payments/pix para criar pagamentos."})

# Rota para criar um pagamento via Pix
@app.route('/payments/pix', methods=['POST']) 
def create_payment_pix():
    data = request.get_json()  # Obtém os dados JSON da requisição

    if not data or 'valor' not in data: # Verifica se os dados estão presentes e se o campo 'valor' está incluído
        return jsonify({"error": "Missing 'valor' in request data"}), 400  # Retorna erro se o valor não estiver presente
    
    # Define a data de expiração como o momento atual (pode ser ajustado conforme necessário)
    expiration_date = datetime.now() + timedelta(hours=30)

    # Cria uma nova instância de Payment com o valor e a data de expiração
    new_payment = Payment(valor=data['valor'], expiration_date=expiration_date) 

    # Cria uma instância da classe Pix
    pix_obj = Pix() 
    data_payment_pix = pix_obj.create_payment()  # Chama o método para criar o pagamento e gerar o QR code
    new_payment.bank_payment_id = data_payment_pix['bank_payment_id']  # Atribui o ID do pagamento retornado pelo banco
    new_payment.qr_code = data_payment_pix['qrcode_path']  # Atribui o caminho do código QR

    db.session.add(new_payment)  # Adiciona o novo pagamento à sessão do banco de dados
    db.session.commit()  # Salva as alterações no banco de dados

    # Emite evento via WebSocket para notificar clientes conectados sobre novo pagamento
    try:
        # Extrai nome do arquivo QR sem extensão
        qr_basename = os.path.basename(new_payment.qr_code)
        qr_name, _ = os.path.splitext(qr_basename)
        socketio.emit('new_payment', {
            'id': new_payment.id,
            'valor': float(new_payment.valor),
            'qr_code': new_payment.qr_code,
            'qr_name': qr_name,
            'payment': new_payment.to_dict()
        }, broadcast=True)
    except Exception:
        # não interrompe a resposta caso o socket falhe
        pass

    # Retorna uma mensagem de sucesso após criar o pagamento
    return jsonify({"message": "Seu Pagamento via Pix foi criado com sucesso!", 
                    "payment": new_payment.to_dict()})


# Rota para obter os detalhes de um pagamento via Pix usando o ID do pagamento
@app.route('/payments/pix/<int:payment_id>', methods=['GET']) 
def payment_pix_page(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return render_template('404.html'), 404
    return render_template('payment_pix.html', payment=payment, host='http://localhost:5000')

# Rota para servir a imagem do código QR
@app.route('/payments/pix/qr_code/<file_name>', methods=['GET'])
def get_image(file_name):
    return send_file(f'static/img/{file_name}.png', mimetype='image/png')  # Retorna a imagem do código QR como resposta

# Rota para confirmar o pagamento via Pix
@app.route('/payments/pix/confirmation', methods=['POST'])
def confirmation_payment_pix():
    data = request.get_json() # Obtém os dados JSON da requisição

    # validação dos dados recebidos
    # Verifica se os dados estão presentes e se os campos 'bank_payment_id' e 'valor' estão incluídos
    if 'bank_payment_id' not in data and 'valor' not in data:
        return jsonify({"erro": "Dados de pagamento inválidos"}), 400

    # Busca pelo campo corretamente mapeado no modelo (`bank_payment_id`)
    payment = Payment.query.filter_by(bank_payment_id=data.get('bank_payment_id')).first()

    # Se o pagamento não for encontrado, retorna um erro 404
    if not payment or payment.pago:
        return jsonify({"erro": "Pagamento não encontrado"}), 404
    
    # Verifica se o valor do pagamento recebido corresponde ao valor esperado
    if data.get('valor') != payment.valor:
        return jsonify({"erro": "Valor do pagamento não corresponde ao valor esperado"}), 400
    
    # Atualiza o status do pagamento para confirmado
    payment.pago = True
    db.session.commit()  # Salva as alterações no banco de dados
    # Emite evento via WebSocket para notificar clientes que o pagamento foi confirmado
    try:
        socketio.emit('payment_confirmed', {
            'id': payment.id,
            'bank_payment_id': payment.bank_payment_id
        }, broadcast=True)
    except Exception:
        pass
    return jsonify({"message": "Pagamento confirmado com sucesso!", "id": payment.id})  


# Rota para exibir a página de confirmação do pagamento via Pix
@app.route('/payments/pix/confirmed/<int:payment_id>', methods=['GET'])
def confirmed_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return render_template('404.html'), 404
    
    amount = f"{payment.valor:.2f}" if payment.valor is not None else "0.00"
    order = payment.id # Atribui o ID do pagamento como o número do pedido

    # Garante que a URL do QR code aponte para a rota de entrega correta.
    # Se `payment.qr_code` contém algo como 'static/img/filename.png', extraímos apenas 'filename'
    qr_basename = os.path.basename(payment.qr_code)
    qr_name, _ext = os.path.splitext(qr_basename)
    qr_url = f'/payments/pix/qr_code/{qr_name}'

    # Formata o valor para exibição com duas casas decimais e vírgula
    amount_display = f"{payment.valor:.2f}".replace('.', ',') if payment.valor is not None else "0,00"

    # Renderiza a página HTML de confirmação do pagamento com os detalhes
    return render_template('confirmed_payment.html',
                           payment=payment,
                           amount=amount_display,
                           host='http://localhost:5000',
                           order=order)  # Renderiza a página HTML de confirmação do pagamento com os detalhes

# Rota para redirecionar para o último pagamento confirmado
@app.route('/payments/pix/confirmed/', methods=['GET'])
def confirmed_latest_redirect():
    
    # Redireciona para o último pagamento criado, se existir
    latest = Payment.query.order_by(Payment.id.desc()).first()
    if not latest:
        return render_template('404.html'), 404
    return redirect(url_for('confirmed_payment', payment_id=latest.id))

# websocket para notificar o cliente sobre a confirmação do pagamento
@socketio.on('confirma_pagamento')
def handle_connect():
    print('Cliente conectado para confirmação de pagamento')

# websocket para notificar o cliente sobre a desconexão
@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado do WebSocket')






# Verifica se o script está sendo executado diretamente (não importado como módulo)
if __name__ == '__main__': 
    with app.app_context():
        db.create_all()
        
    # Use socketio.run for proper WebSocket support (invoca o servidor apropriado)
    socketio.run(app, debug=True)