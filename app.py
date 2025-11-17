import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from urllib.parse import quote 

# --- CONFIGURAÇÕES GERAIS ---
app = Flask(__name__) 
DATABASE = 'database.db'
DATE_FORMAT = '%d/%m/%Y %H:%M'

# 🟢 SEU NÚMERO DE WHATSAPP (55 + DDD + NÚMERO)
MEU_WHATSAPP_NUMBER = "5534974008823" 

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


# --- ROTA PRINCIPAL: AGENDAMENTO E VISUALIZAÇÃO ---

@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()
    
    if request.method == 'POST':
        cliente = request.form['cliente']
        placa = request.form['placa'].upper()
        
        # Captura das variáveis dos campos dinâmicos
        tipo_veiculo = request.form['tipo_veiculo'] 
        servico = request.form['servico']
        
        # Converte a data
        data_hora_iso = request.form['data_hora_input']
        try:
            dt_obj = datetime.strptime(data_hora_iso, '%Y-%m-%dT%H:%M')
            data_hora_str = dt_obj.strftime(DATE_FORMAT)
        except ValueError:
            data_hora_str = None
        
        if data_hora_str:
            try:
                # Verifica Conflito e Salva
                conflito = conn.execute(
                    "SELECT * FROM agendamentos WHERE data_hora_str = ?", (data_hora_str,)
                ).fetchone()
                
                if not conflito:
                    # SALVA NO BANCO DE DADOS
                    conn.execute(
                        "INSERT INTO agendamentos (cliente, placa, servico, data_hora_str) VALUES (?, ?, ?, ?)",
                        (cliente, placa, servico, data_hora_str)
                    )
                    conn.commit()
                    
                    # CRIA A MENSAGEM DO WHATSAPP
                    mensagem = (
                        f"✅ NOVO AGENDAMENTO SITE!\n\n"
                        f"Cliente: {cliente}\n"
                        f"Tipo de Veículo: {tipo_veiculo}\n" 
                        f"Placa: {placa}\n"
                        f"Serviço Escolhido: {servico}\n" 
                        f"Data/Hora: {data_hora_str}"
                    )
                    
                    mensagem_codificada = quote(mensagem)
                    whatsapp_url = f"https://wa.me/{MEU_WHATSAPP_NUMBER}?text={mensagem_codificada}"

                    conn.close()
                    return redirect(whatsapp_url)

            except ValueError:
                pass
            
    # Lógica GET
    agendamentos = conn.execute(
        "SELECT * FROM agendamentos ORDER BY data_hora_str"
    ).fetchall()
    
    conn.close()
    return render_template('index.html', agendamentos=agendamentos)

# --- Execução da Aplicação ---
if __name__ == '__main__':
    app.run(debug=True)