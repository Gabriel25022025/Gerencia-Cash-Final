# database.py
import sqlite3, config
from datetime import datetime, timedelta

def get_db_connection():
    db_path = config.DATABASE_NAME
    # Versão correta para o Render: não criamos o diretório, apenas conectamos.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, valor REAL NOT NULL, descricao TEXT, categoria TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    conn.execute('CREATE TABLE IF NOT EXISTS usuarios (user_id TEXT PRIMARY KEY, saldo_inicial REAL NOT NULL, data_definicao DATE NOT NULL);')
    conn.execute('CREATE TABLE IF NOT EXISTS clientes (user_id TEXT PRIMARY KEY, plano TEXT NOT NULL, status_assinatura TEXT NOT NULL, data_fim_assinatura DATE NOT NULL);')
    conn.execute('CREATE TABLE IF NOT EXISTS gastos_fixos (id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, valor REAL NOT NULL, descricao TEXT NOT NULL);')
    conn.execute('CREATE TABLE IF NOT EXISTS orcamentos (user_id TEXT NOT NULL, categoria TEXT NOT NULL, valor REAL NOT NULL, PRIMARY KEY (user_id, categoria));')
    conn.commit()
    conn.close()

def ativar_cliente(user_id, plano, duracao_dias):
    conn = get_db_connection()
    data_fim = datetime.now().date() + timedelta(days=duracao_dias)
    status = 'trial' if plano == 'trial' else 'ativa'
    conn.execute("INSERT OR REPLACE INTO clientes (user_id, plano, status_assinatura, data_fim_assinatura) VALUES (?, ?, ?, ?)", (user_id, plano, status, data_fim))
    conn.commit(); conn.close()
    print(f"Cliente {user_id} ativado no plano {plano}. Acesso até {data_fim.strftime('%d/%m/%Y')}.")

def get_cliente(user_id):
    conn = get_db_connection()
    cliente = conn.execute("SELECT * FROM clientes WHERE user_id = ?", (user_id,)).fetchone()
    if not cliente:
        conn.close(); return None
    data_fim = datetime.strptime(cliente['data_fim_assinatura'], '%Y-%m-%d').date()
    if cliente['status_assinatura'] in ['ativa', 'trial'] and datetime.now().date() > data_fim:
        conn.execute("UPDATE clientes SET status_assinatura = 'vencido' WHERE user_id = ?", (user_id,))
        conn.commit()
        cliente = conn.execute("SELECT * FROM clientes WHERE user_id = ?", (user_id,)).fetchone()
    conn.close(); return cliente

def get_todos_clientes_ativos():
    conn = get_db_connection()
    clientes = conn.execute("SELECT user_id, plano FROM clientes WHERE status_assinatura = 'ativa' AND date(data_fim_assinatura) >= date('now')").fetchall()
    conn.close(); return clientes

def set_orcamento(user_id, categoria, valor):
    conn=get_db_connection();conn.execute("INSERT OR REPLACE INTO orcamentos (user_id, categoria, valor) VALUES (?, ?, ?)",(user_id, categoria, valor));conn.commit();conn.close()
def get_orcamentos(user_id):
    conn=get_db_connection();orcamentos=conn.execute("SELECT categoria, valor FROM orcamentos WHERE user_id = ?",(user_id,)).fetchall();conn.close();return {orc['categoria']:orc['valor'] for orc in orcamentos}
def search_gastos(user_id,termo):
    conn=get_db_connection();termo_busca=f"%{termo}%";gastos=conn.execute("SELECT id, valor, descricao, categoria, data_hora FROM gastos WHERE user_id = ? AND descricao LIKE ? ORDER BY data_hora DESC",(user_id,termo_busca)).fetchall();conn.close();return gastos
def set_saldo(user_id,saldo):
    conn=get_db_connection();conn.execute("INSERT OR REPLACE INTO usuarios (user_id, saldo_inicial, data_definicao) VALUES (?, ?, ?)",(user_id,saldo,datetime.now().date()));conn.commit();conn.close()
def add_to_saldo(user_id,valor_adicionar):
    conn=get_db_connection();cursor=conn.cursor();cursor.execute("SELECT saldo_inicial FROM usuarios WHERE user_id = ?",(user_id,));
    if cursor.fetchone() is None: conn.close();return False
    conn.execute("UPDATE usuarios SET saldo_inicial = saldo_inicial + ? WHERE user_id = ?",(valor_adicionar,user_id));conn.commit();conn.close();return True
def get_saldo(user_id):
    conn=get_db_connection();saldo_info=conn.execute("SELECT saldo_inicial FROM usuarios WHERE user_id = ?",(user_id,)).fetchone();conn.close();return saldo_info
def add_gasto_fixo(user_id,valor,descricao):
    conn=get_db_connection();conn.execute("INSERT INTO gastos_fixos (user_id, valor, descricao) VALUES (?, ?, ?)",(user_id,valor,descricao));conn.commit();conn.close()
def get_gastos_fixos(user_id):
    conn=get_db_connection();gastos_fixos=conn.execute("SELECT id, valor, descricao FROM gastos_fixos WHERE user_id = ? ORDER BY valor DESC",(user_id,)).fetchall();conn.close();return gastos_fixos
def remove_gasto_fixo(user_id,gasto_id):
    conn=get_db_connection();cursor=conn.execute("DELETE FROM gastos_fixos WHERE id = ? AND user_id = ?",(gasto_id,user_id));conn.commit();conn.close();return cursor.rowcount > 0
def add_gasto(user_id,valor,descricao,categoria):
    conn=get_db_connection();conn.execute("INSERT INTO gastos (user_id, valor, descricao, categoria) VALUES (?, ?, ?, ?)",(user_id,valor,descricao,categoria));conn.commit();conn.close()
def get_gastos_do_mes(user_id):
    conn=get_db_connection();agora=datetime.now();primeiro_dia_mes=agora.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    gastos=conn.execute("SELECT id, valor, descricao, categoria, data_hora FROM gastos WHERE user_id = ? AND data_hora >= ? ORDER BY data_hora ASC",(user_id,primeiro_dia_mes)).fetchall();conn.close();return gastos
def remove_gasto_by_id(user_id,gasto_id):
    conn=get_db_connection();cursor=conn.execute("DELETE FROM gastos WHERE id = ? AND user_id = ?",(gasto_id,user_id));conn.commit();conn.close();return cursor.rowcount > 0
def delete_last_gasto(user_id):
    conn=get_db_connection();gasto=conn.execute("SELECT id FROM gastos WHERE user_id = ? ORDER BY data_hora DESC LIMIT 1",(user_id,)).fetchone();conn.close()
    if not gasto:return False
    return remove_gasto_by_id(user_id,gasto['id'])
def delete_all_gastos(user_id):
    conn=get_db_connection();conn.execute("DELETE FROM gastos WHERE user_id = ?",(user_id,));conn.execute("DELETE FROM usuarios WHERE user_id = ?",(user_id,));conn.execute("DELETE FROM gastos_fixos WHERE user_id = ?",(user_id,));conn.execute("DELETE FROM clientes WHERE user_id = ?",(user_id,));conn.execute("DELETE FROM orcamentos WHERE user_id = ?",(user_id,));conn.commit();conn.close()