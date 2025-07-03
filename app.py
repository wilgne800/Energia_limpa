from flask import Flask, request, jsonify, render_template
import requests
import os
import secrets
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Contexto da IA
BOT_CONTEXT = """
Você é Italo um vendedor especializado da empresa Energia Alagoana, conversando com representantes de empresas que desejam economizar na conta de luz e valorizar sua marca com responsabilidade ambiental.

INFORMAÇÕES IMPORTANTES:
- Oferecemos energia 100% renovável sem necessidade de instalação
- Economia de até 20% na conta de energia
- Créditos aplicados diretamente na fatura da distribuidora Equatorial
- Processo simples: primeiro um comprovante de energia e aguardar a aprovação
- logo apos  assinatura contratual e envio de documentos do CNPJ
- Sem custos iniciais ou investimento em equipamentos

DIRETRIZES DE RESPOSTA:
1. Seja educado, profissional e consultivo
2. Mantenha respostas claras e objetivas (3-5 linhas)
3. Destaque os benefícios econômicos e sustentáveis
4. Se não souber responder, sugira contato via formulário
5. Finalize sempre reforçando os benefícios
6. Não mande mensagens muito grande, mande mensagens curtas
7. Perceba quando a conversa está pronta pra acabar e fale para o cliente aguardar
"""

# Credenciais do Gemini e Z-API (usando .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyCOif8UqGDkjtswQfe-rIkD4ZEX0upoqXg"

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")
NGROK_URL = os.getenv("NGROK_URL")

API_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
API_URL_BOTOES = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-button-list"
ZAPI_WEBHOOK_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/webhook"

WEBHOOK_TOKEN = secrets.token_urlsafe(32)

# Funções auxiliares
def generate_gemini_response(user_message):
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{BOT_CONTEXT}\n\nCliente: {user_message}\n\nResposta:"
            }]
        }]
    }
    response = requests.post(GEMINI_URL, json=payload, headers={'Content-Type': 'application/json'})
    return response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

def send_whatsapp_message(phone, message):
    headers = {'Client-Token': CLIENT_TOKEN, 'Content-Type': 'application/json'}
    payload = {"phone": phone, "message": message}
    return requests.post(API_URL, json=payload, headers=headers).json()

def padronizar_numero(numero):
    numero_limpo = ''.join(filter(str.isdigit, numero))
    return numero_limpo if numero_limpo.startswith('55') else '55' + numero_limpo

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Por favor, digite sua mensagem'}), 400

        bot_response = generate_gemini_response(user_message)
        return jsonify({'response': bot_response})

    except Exception as e:
        return jsonify({'error': f"Erro interno: {str(e)}"}), 500

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not all([name, email, phone, subject, message]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

        subject_map = {
            'commercial': 'Dúvidas Comerciais',
            'support': 'Suporte Técnico',
            'partnership': 'Parcerias',
            'other': 'Outros'
        }
        subject_text = subject_map.get(subject, 'Outros')

        confirmation = (
            f"*Confirmação de Contato - Energia Alagoana*\n\n"
            f"Olá {name}, recebemos seu contato!\n\n"
            f"*Detalhes:*\n"
            f"📧 E-mail: {email}\n📞 Telefone: {phone}\n📌 Assunto: {subject_text}\n💬 Mensagem: {message}\n\n"
            f"Escolha uma opção para continuar:" )

        payload = {
            "phone": padronizar_numero(phone),
            "message": confirmation,
            "buttonList": {
                "title": "Opções de Atendimento",
                "buttons": [
                    {"id": "1", "label": "1 - Falar com assistente virtual"},
                    {"id": "3", "label": "2 - Aguardar uma pessoa física"},
                    {"id": "4", "label": "3 - Me liguem!"}
                ]
            }
        }

        headers = {'Content-Type': 'application/json', 'Client-Token': CLIENT_TOKEN}
        response = requests.post(API_URL_BOTOES, json=payload, headers=headers)

        if response.status_code != 200:
            return jsonify({'error': 'Erro ao enviar via Z-API'}), 500

        return jsonify({'success': True, 'message': 'Formulário enviado com sucesso! Aguarde contato no WhatsApp.'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        bill_amount = float(data['bill_amount'])
        consumer_type = data['consumer_type']

        savings_percent = 0.15 if consumer_type == 'residential' else 0.20
        monthly_savings = bill_amount * savings_percent
        discounted_value = bill_amount - monthly_savings
        annual_savings = monthly_savings * 12

        return jsonify({
            'original_value': f"R$ {bill_amount:,.2f}",
            'discounted_value': f"R$ {discounted_value:,.2f}",
            'monthly_savings': f"R$ {monthly_savings:,.2f}",
            'annual_savings': f"R$ {annual_savings:,.2f}",
            'savings_percent': f"{savings_percent * 100:.0f}%"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

RECENT_MESSAGES = {}
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("📨 Webhook recebido:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Verificar se é uma mensagem válida
        if not data.get("phone"):
            return jsonify({"status": "ignored - no phone"}), 200
            # Verificar duplicata
        message_id = data.get("messageId")
        if message_id in RECENT_MESSAGES:
            return jsonify({"status": "ignored - duplicate"}), 200
            # Armazenar ID da mensagem por 60 segundos
        RECENT_MESSAGES[message_id] = datetime.now()

        # Limpar mensagens antigas
        for msg_id in list(RECENT_MESSAGES.keys()):
            if datetime.now() - RECENT_MESSAGES[msg_id] > timedelta(minutes=1):
                del RECENT_MESSAGES[msg_id]

        numero = data.get("phone")
        texto = ""

        # Captura resposta de botão (se clicou em algum botão)
        if data.get("buttonsResponseMessage", {}).get("buttonId"):
            button_id = data["buttonsResponseMessage"]["buttonId"].strip()

            # Respostas para cada botão
            if button_id == "1":
                resposta = generate_gemini_response("Cliente quer falar com assistente virtual")
                send_whatsapp_message(numero, resposta)
            elif button_id == "2":
                resposta = "Agradecemos pelo seu contato! Um de nossos representantes entrará em contato em breve. Por favor, aguarde."
                send_whatsapp_message(numero, resposta)
            elif button_id == "3":
                resposta = "Obrigado pelo interesse! Vamos direcionar seu contato para nossa equipe comercial que entrará em contato pelo telefone informado o mais breve possível."
                send_whatsapp_message(numero, resposta)
            else:
                print(f"⏹ Botão {button_id} pressionado - IA não responde.")
            return jsonify({"status": "ok"}), 200

        # Captura mensagem de texto normal (se digitou algo)
        elif data.get("text", {}).get("message"):
            texto = data["text"]["message"].strip()
            resposta = generate_gemini_response(texto)
            send_whatsapp_message(numero, resposta)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"❌ Erro no webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    print(f"🔑 Token do Webhook: {WEBHOOK_TOKEN}")
    print(f"🌐 URL do Webhook: {NGROK_URL}/webhook")
    app.run(port=5000, debug=True)
