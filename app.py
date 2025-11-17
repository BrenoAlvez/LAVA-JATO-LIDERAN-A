import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta # Adicionado timedelta para duração do evento
from urllib.parse import quote 

# ######################################################################
# ATENÇÃO: IMPORTAÇÕES NECESSÁRIAS PARA O GOOGLE CALENDAR API
# As bibliotecas abaixo (google-auth, google-api-python-client) devem
# ser instaladas via pip, mas o código de autenticação (OAuth) 
# É OMITIDO aqui por ser complexo e depender de arquivos externos (token.json).
# ######################################################################

# --- CONFIGURAÇÕES GERAIS ---
app = Flask(__name__) 
DATABASE = 'database.db'
DATE_FORMAT = '%d/%m/%Y %H:%M'

# 🟢 SEU NÚMERO DE WHATSAPP (55 + DDD + NÚMERO)
MEU_WHATSAPP_NUMBER = "5534974008823" 

# ⚠️ PLACEHOLDER: ID DA SUA AGENDA (Obtido no Google Calendar)
# Este é o ID da agenda "Lava Jato Liderança" que você criou.
CALENDAR_ID = 'SEU_ID_DE_AGENDA_AQUI@group.calendar.google.com' 


# --- Funções de Banco de Dados ---
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados criando a tabela de agendamentos."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            placa TEXT NOT NULL,
            servico TEXT NOT NULL,
            data_hora_str TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()


# --- NOVA FUNÇÃO: AGENDAMENTO NO GOOGLE CALENDAR ---
def create_calendar_event(cliente, placa, servico, data_hora_str):
    """
    Tenta criar um evento no Google Calendar.
    
    ⚠️ ATENÇÃO: Esta é a função que precisa ser preenchida com o código REAL da API 
    do Google Calendar (autenticação e chamada). O código abaixo é apenas um esqueleto.
    """
    
    # 1. CONVERTER DATA PARA O FORMATO ISO (REQUERIDO PELA API)
    try:
        # Tenta converter o formato da DB para o objeto datetime
        dt_obj = datetime.strptime(data_hora_str, DATE_FORMAT)
        iso_start = dt_obj.isoformat()
        # Assumimos que o serviço dura 1 hora
        iso_end = (dt_obj + timedelta(hours=1)).isoformat() 
    except Exception as e:
        print(f"Erro na conversão de data: {e}")
        return False

    event_body = {
        'summary': f'Lava-Jato: {servico} - {cliente}',
        'location': f'Placa: {placa}',
        'description': f'Agendado via site. Cliente: {cliente}',
        'start': {'dateTime': iso_start, 'timeZone': 'America/Sao_Paulo'}, # Use seu fuso horário
        'end': {'dateTime': iso_end, 'timeZone': 'America/Sao_Paulo'},
        'attendees': [
            # Opcional: Notifica o e-mail do cliente, se você tivesse esse campo
        ],
    }

    # -----------------------------------------------------------
    # 2. CÓDIGO DA API DO GOOGLE CALENDAR VAI AQUI
    # EXEMPLO:
    # 
    # creds = obter_credenciais() # Função complexa de autenticação
    # service = build('calendar', 'v3', credentials=creds)
    # event = service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
    # -----------------------------------------------------------

    # Por enquanto, apenas simula sucesso:
    print(f"✅ EVENTO SIMULADO: {event_body['summary']}")
    # Mude para True para simular sucesso, ou False para simular falha na integração real
    return True 


# --- ROTA PRINCIPAL: AGENDAMENTO E VISUALIZAÇÃO (Atualizada) ---

@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()
    
    if request.method == 'POST':
        cliente = request.form['cliente']
        placa = request.form['placa'].upper()
        tipo_veiculo = request.form['tipo_veiculo'] 
        servico = request.form['servico']
        
        # Converte a data
        data_hora_iso = request.form['data_hora_input']
        data_hora_str = None
        try:
            dt_obj = datetime.strptime(data_hora_iso, '%Y-%m-%dT%H:%M')
            data_hora_str = dt_obj.strftime(DATE_FORMAT)
        except ValueError:
            pass
        
        if data_hora_str:
            try:
                # 1. Verifica Conflito no Banco de Dados (opcionalmente você faria aqui a verificação no Calendar)
                conflito = conn.execute(
                    "SELECT * FROM agendamentos WHERE data_hora_str = ?", (data_hora_str,)
                ).fetchone()
                
                if not conflito:
                    
                    # 2. TENTA AGENDAR NO GOOGLE CALENDAR (NOVA CHAMADA)
                    calendar_success = create_calendar_event(cliente, placa, servico, data_hora_str)
                    
                    # 3. SALVA NO BANCO DE DADOS LOCAL
                    conn.execute(
                        "INSERT INTO agendamentos (cliente, placa, servico, data_hora_str) VALUES (?, ?, ?, ?)",
                        (cliente, placa, servico, data_hora_str)
                    )
                    conn.commit()
                    
                    # 4. CRIA A MENSAGEM DO WHATSAPP (ATUALIZADA)
                    if calendar_success:
                        status_msg = "✅ AGENDAMENTO CONFIRMADO E ADICIONADO À AGENDA!"
                    else:
                        status_msg = "⚠️ AGENDAMENTO REGISTRADO, MAS HOUVE ERRO NA AGENDA GOOGLE."
                        
                    mensagem = (
                        f"{status_msg}\n\n"
                        f"Cliente: {cliente}\n"
                        f"Tipo de Veículo: {tipo_veiculo}\n" 
                        f"Placa: {placa}\n"
                        f"Serviço Escolhido: {servico}\n" 
                        f"Data/Hora: {data_hora_str}"
                    )
                    
                    mensagem_codificada = quote(mensagem)
                    whatsapp_url = f"https://wa.me/{MEU_WHATSAPP_NUMBER}?text={mensagem_codificada}"

                    conn.close()
                    # Redireciona para o WhatsApp (ou para uma página de confirmação final)
                    return redirect(whatsapp_url)

            except ValueError:
                pass
            
    # Lógica GET: Exibir agendamentos
    agendamentos = conn.execute(
        "SELECT * FROM agendamentos ORDER BY data_hora_str"
    ).fetchall()
    
    conn.close()
    return render_template('index.html', agendamentos=agendamentos)

# --- Execução da Aplicação (Deve ser removida para o deploy no PythonAnywhere) ---
# if __name__ == '__main__':
#     app.run(debug=True)