# API-Pix-simulada-

API em Flask que simula criação de pagamentos via Pix, gera QR code localmente, persiste pagamentos em SQLite e notifica clientes em tempo real via Socket.IO.

---

## Visão geral

Este projeto implementa uma API de pagamentos Pix simulada com as seguintes responsabilidades:

- Criar pagamento e gerar QR code (arquivo PNG salvo em `static/img`).
- Persistir pagamentos em SQLite (`instance/payments.db`).
- Confirmar pagamentos via endpoint (recebe notificações do "banco" simulado).
- Notificar clientes conectados em tempo real via Socket.IO (`new_payment`, `payment_confirmed`).
- Páginas HTML simples para exibir o QR e a confirmação.

O objetivo é fornecer um backend leve para desenvolvimento e testes de frontends que consumam fluxo de pagamentos com QR e WebSocket.

---

## Tecnologias

- Python 3.11+
- Flask
- Flask-SocketIO
- Flask-SQLAlchemy (SQLite)
- qrcode + Pillow (para gerar imagens QR)
- pytest (testes)
