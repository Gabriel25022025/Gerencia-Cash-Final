# commands.py

import database as db
from datetime import datetime, timedelta
from twilio.rest import Client
import config
from collections import defaultdict

def enviar_mensagem_boas_vindas(user_id, plano):
    link_plano = config.LINKS_AREA_DE_MEMBROS.get(plano)
    if plano == 'trial':
        link_plano = config.LINKS_AREA_DE_MEMBROS.get('diamante')
    if not link_plano:
        link_plano = "https://seusite.com/area-de-membros"

    if plano == 'trial':
        mensagem = (f"🎉 Bem-vindo(a) ao GerenciaCash!\n\n"
                    f"Você iniciou seu período de teste de 7 dias com todos os recursos do Plano Diamante liberados!\n\n"
                    f"Use `ajuda` para ver os comandos.\n\nAcesse sua área de membros aqui:\n{link_plano}")
    else:
        mensagem = (f"🎉 Agradecemos por sua assinatura do *GerenciaCash*!\n\nSeu acesso ao *Plano {plano.capitalize()}* foi liberado.\n\n"
                    f"Parabéns por essa escolha incrível! Seu bot pessoal já está pronto para te ajudar a tomar o controle de suas finanças.\n\n"
                    f"Acesse sua área de membros exclusiva e descubra como aproveitar cada função ao máximo:\n{link_plano}\n\nPara começar, envie `ajuda`.")
    try:
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        message = client.messages.create(from_=config.TWILIO_WHATSAPP_NUMBER, body=mensagem, to=user_id)
        print(f"Mensagem de boas-vindas enviada com sucesso para {user_id}.")
    except Exception as e:
        print(f"ERRO ao enviar boas-vindas para {user_id}: {e}")

def exportar_dados(user_id):
    gastos = db.get_gastos_do_mes(user_id)
    if not gastos: return "Nenhum gasto registrado este mês para exportar."
    csv_data = "Data,Valor,Descricao,Categoria\n"
    for gasto in gastos:
        data_local = datetime.strptime(gasto['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'); valor = str(gasto['valor']).replace('.', ','); descricao = f"\"{gasto['descricao']}\""; categoria = gasto['categoria'] if gasto['categoria'] else "N/A"
        csv_data += f"{data_local},{valor},{descricao},{categoria}\n"
    return f"Copie e cole o texto abaixo em um arquivo de texto e salve como `export.csv`:\n\n```{csv_data}```"

def gerar_relatorio_semanal(user_id):
    agora = datetime.now(); inicio_semana = agora - timedelta(days=agora.weekday()); gastos = db.get_gastos_do_mes(user_id)
    gastos_semana = [g for g in gastos if datetime.strptime(g['data_hora'], '%Y-%m-%d %H:%M:%S') >= inicio_semana]
    if not gastos_semana: return None
    total_gasto = sum(g['valor'] for g in gastos_semana)
    resposta = f"💎 *Seu Relatório Semanal GerenciaCash*\n\nOlá! Você gastou *R$ {total_gasto:.2f}* esta semana.\n\nResumo por categoria:\n"
    somas_por_categoria = defaultdict(float)
    for gasto in gastos_semana: somas_por_categoria[gasto['categoria'] or '#outros'] += gasto['valor']
    for categoria, soma in somas_por_categoria.items(): resposta += f"• {categoria}: R$ {soma:.2f}\n"
    resposta += "\nContinue no controle!"; return resposta

def gerenciar_orcamento(user_id, mensagem):
    try:
        partes = mensagem.split(); categoria = next((p for p in partes if p.startswith('#')), None)
        if not categoria:
            if len(partes) == 1 and partes[0] == "orçamento": return status_orcamento(user_id)
            return "❌ Formato inválido. Use `orçamento #categoria VALOR`."
        valor_str = partes[-1].replace(',', '.'); valor = float(valor_str)
        db.set_orcamento(user_id, categoria, valor); return f"✅ Orçamento para `{categoria}` definido em *R$ {valor:.2f}*."
    except (ValueError, IndexError): return "❌ Formato inválido."

def status_orcamento(user_id):
    orcamentos = db.get_orcamentos(user_id)
    if not orcamentos: return "Nenhum orçamento definido."
    gastos_por_categoria = resumo_categorias(user_id, apenas_dados=True)
    resposta = "📊 *Status dos Orçamentos do Mês*\n--------------------\n"
    for categoria, valor_orcado in orcamentos.items():
        valor_gasto = gastos_por_categoria.get(categoria, 0.0); percentual = (valor_gasto / valor_orcado) * 100 if valor_orcado > 0 else 0
        emoji = "✅";
        if percentual > 100: emoji = "🆘"
        elif percentual >= 90: emoji = "⚠️"
        resposta += f"{emoji} {categoria}: R$ {valor_gasto:.2f} / R$ {valor_orcado:.2f} (*{percentual:.0f}%*)\n"
    return resposta

def pesquisar_gastos(user_id, mensagem):
    try:
        termo = " ".join(mensagem.split()[1:])
        if not termo: return "❌ Faltou o termo de busca."
        resultados = db.search_gastos(user_id, termo)
        if not resultados: return f"Nenhum gasto encontrado com o termo '{termo}'."
        resposta = f"🔎 Resultados para '{termo}':\n--------------------\n"
        for gasto in resultados:
            data_local = datetime.strptime(gasto['data_hora'], '%Y-%m-%d %H:%M:%S'); cat_str = f" {gasto['categoria']}" if gasto['categoria'] else ""
            resposta += f"🗓️ {data_local.strftime('%d/%m/%y')} - R$ {gasto['valor']:.2f} - {gasto['descricao']}{cat_str}\n"
        return resposta
    except IndexError: return "❌ Formato inválido."

def definir_saldo_inicial(user_id, mensagem):
    try:
        partes = mensagem.split(); valor_str = partes[-1].replace(',', '.'); valor = float(valor_str)
        db.set_saldo(user_id, valor); return f"✅ Saldo inicial definido para *R$ {valor:.2f}*."
    except (ValueError, IndexError): return "❌ Formato inválido."

def adicionar_ao_saldo(user_id, mensagem):
    try:
        partes = mensagem.split(); valor_str = partes[-1].replace(',', '.'); valor = float(valor_str)
        if db.add_to_saldo(user_id, valor): return f"✅ Adicionado *R$ {valor:.2f}* ao seu saldo."
        else: return "❌ Você precisa definir um saldo inicial primeiro."
    except (ValueError, IndexError): return "❌ Formato inválido."

def verificar_saldo_atual(user_id):
    saldo_info = db.get_saldo(user_id)
    if not saldo_info: return "Você ainda não definiu um saldo inicial."
    saldo_inicial = saldo_info['saldo_inicial']; gastos_do_mes = db.get_gastos_do_mes(user_id); total_gastos_variaveis = sum(g['valor'] for g in gastos_do_mes)
    gastos_fixos = db.get_gastos_fixos(user_id); total_gastos_fixos = sum(g['valor'] for g in gastos_fixos)
    saldo_disponivel = saldo_inicial - total_gastos_variaveis - total_gastos_fixos
    return f"💰 *Balanço Real do Mês*\n--------------------\n" + f"Saldo Inicial: R$ {saldo_inicial:.2f}\n" + f"Gastos Fixos: - R$ {total_gastos_fixos:.2f}\n" + f"Gastos Variáveis: - R$ {total_gastos_variaveis:.2f}\n" + "--------------------\n" + f"SALDO DISPONÍVEL: *R$ {saldo_disponivel:.2f}*"

def gerenciar_gasto_fixo(user_id, mensagem):
    partes = mensagem.split();
    if len(partes)<3:
        if len(partes)==2 and partes[1]=="fixo": return listar_gastos_fixos(user_id)
        return "❌ Comando inválido. Use `gasto fixo listar`, `adicionar` ou `remover`."
    sub_comando = partes[2]
    if sub_comando == "adicionar":
        try:
            valor_str = partes[3].replace(',', '.'); valor = float(valor_str); descricao = " ".join(partes[4:])
            if not descricao: return "❌ Faltou a descrição."
            db.add_gasto_fixo(user_id, valor, descricao); return f"✅ Gasto fixo '{descricao}' (R$ {valor:.2f}) adicionado."
        except (ValueError, IndexError): return "❌ Formato inválido."
    elif sub_comando == "remover":
        try:
            gasto_id = int(partes[3])
            if db.remove_gasto_fixo(user_id, gasto_id): return f"✅ Gasto fixo com ID [{gasto_id}] removido."
            else: return f"❌ Gasto fixo com ID [{gasto_id}] não encontrado."
        except (ValueError, IndexError): return "❌ Formato inválido."
    else: return listar_gastos_fixos(user_id)

def listar_gastos_fixos(user_id):
    gastos_fixos = db.get_gastos_fixos(user_id)
    if not gastos_fixos: return "Nenhum gasto fixo definido."
    resposta = " GASTOS FIXOS MENSAIS \n--------------------\n"; total = 0.0
    for gasto in gastos_fixos: resposta += f"🆔 *[{gasto['id']}]* - R$ {gasto['valor']:.2f} - {gasto['descricao']}\n"; total += gasto['valor']
    return resposta + f"--------------------\nTotal Fixo: *R$ {total:.2f}*"

def adicionar_gasto(user_id, mensagem):
    try:
        partes = mensagem.split();
        if len(partes) < 2: raise ValueError()
        valor_str = partes[1].replace(',', '.'); valor = float(valor_str); descricao_completa = partes[2:]; categoria = None; descricao_final = []
        for parte in descricao_completa:
            if parte.startswith('#'): categoria = parte
            else: descricao_final.append(parte)
        descricao = " ".join(descricao_final) if descricao_final else "Sem descrição"
        db.add_gasto(user_id, valor, descricao, categoria)
        resposta_final = f"✅ Gasto de R$ {valor:.2f} ({descricao}) registrado"
        if categoria:
            resposta_final += f" na categoria {categoria}."
            cliente = db.get_cliente(user_id)
            if cliente and cliente['plano'] in ['ouro', 'diamante', 'trial']:
                orcamentos = db.get_orcamentos(user_id)
                if categoria in orcamentos:
                    gastos_na_categoria = resumo_categorias(user_id, apenas_dados=True).get(categoria, 0.0)
                    orcamento_categoria = orcamentos[categoria]
                    percentual = (gastos_na_categoria / orcamento_categoria) * 100
                    if percentual > 100: resposta_final += f"\n🆘 *Atenção! Você estourou o orçamento de R$ {orcamento_categoria:.2f} para {categoria}!*"
                    elif percentual >= 90: resposta_final += f"\n⚠️ *Aviso: Você já usou {percentual:.0f}% do seu orçamento para {categoria}.*"
        return resposta_final
    except (ValueError): return "❌ Formato inválido."

def listar_gastos(user_id):
    gastos = db.get_gastos_do_mes(user_id);
    if not gastos: return "Nenhum gasto registrado este mês."
    resposta = " GASTOS VARIÁVEIS (Mês Atual) \n--------------------\n"
    for gasto in gastos:
        data_local = datetime.strptime(gasto['data_hora'], '%Y-%m-%d %H:%M:%S'); cat_str = f" {gasto['categoria']}" if gasto['categoria'] else ""
        resposta += f"🆔 *[{gasto['id']}]* - {data_local.strftime('%d/%m')} - R$ {gasto['valor']:.2f} - {gasto['descricao']}{cat_str}\n"
    return resposta + f"\nPara remover, use `remover ID`."

def resumo_categorias(user_id, apenas_dados=False):
    gastos = db.get_gastos_do_mes(user_id); somas_por_categoria = defaultdict(float)
    if not gastos and apenas_dados: return somas_por_categoria
    total_mes = sum(g['valor'] for g in gastos)
    for gasto in gastos:
        categoria = gasto['categoria'] if gasto['categoria'] else '#semcategoria'
        somas_por_categoria[categoria] += gasto['valor']
    if apenas_dados: return somas_por_categoria
    if total_mes == 0: return "Nenhum gasto registrado este mês para resumir."
    categorias_ordenadas = sorted(somas_por_categoria.items(), key=lambda item: item[1], reverse=True)
    resposta = f"📊 *Resumo por Categoria (Mês)*\n--------------------\n"
    for cat, soma in categorias_ordenadas: percentual = (soma / total_mes) * 100; resposta += f"{cat}: R$ {soma:.2f} ({percentual:.1f}%)\n"
    return resposta + "--------------------\n" + f"Total Variável do Mês: *R$ {total_mes:.2f}*"

def remover_gasto(user_id, mensagem):
    try:
        id_remover = int(mensagem.split()[1]);
        if db.remove_gasto_by_id(user_id, id_remover): return f"✅ Gasto com ID [{id_remover}] removido."
        else: return f"❌ Gasto com ID [{id_remover}] não encontrado."
    except (ValueError, IndexError): return "❌ Formato inválido. Use `remover ID`."

def desfazer_ultima_adicao(user_id):
    if db.delete_last_gasto(user_id): return "✅ Último gasto desfeito."
    else: return "🤷‍♂️ Nenhum gasto para desfazer."
def limpar_dados_executar(user_id):
    db.delete_all_gastos(user_id); return "🗑️ Todos os seus dados de gastos foram apagados."

# --- FUNÇÃO DE AJUDA ATUALIZADA E CONCISA ---
def mostrar_ajuda(plano):
    """Gera um menu de ajuda conciso, servindo como um lembrete rápido dos comandos."""
    emojis = {'bronze': '🥉', 'prata': '🥈', 'ouro': '🥇', 'diamante': '💎', 'trial': '💎'}
    emoji_plano = emojis.get(plano, '⚙️')
    
    partes = []
    
    titulo = f"*🤖 GerenciaCash - Comandos {emoji_plano}*\n"
    if plano == 'trial':
        titulo += "_Você está no período de teste (acesso Diamante)._\n"
    else:
        titulo += f"_Seu plano: {plano.capitalize()}_\n"
    partes.append(titulo)

    # Seção Básica (Bronze+)
    partes.append("""
--- *Saldo e Gastos* ---
`saldo inicial VALOR`
`adicionar saldo VALOR`
`saldo`
`gasto VALOR [descrição]`
`listar`
`remover ID`
`desfazer`
""")

    # Seção Prata+
    if plano in ['prata', 'ouro', 'diamante', 'trial']:
        partes.append("""
--- *Organização (Prata+)* ---
`gasto VALOR DESC #cat`
`resumo`
`gasto fixo listar`
`gasto fixo adicionar VALOR DESC`
`gasto fixo remover ID`
""")

    # Seção Ouro+
    if plano in ['ouro', 'diamante', 'trial']:
        partes.append("""
--- *Análise (Ouro+)* ---
`orçamento #cat VALOR`
`orçamento`
`pesquisar TERMO`
""")

    # Seção Diamante+
    if plano in ['diamante', 'trial']:
        partes.append("""
--- *Premium (Diamante)* ---
`exportar`
_(Relatórios semanais automáticos)_
""")
        
    # Rodapé
    partes.append("""
--- *Outros* ---
`limpar tudo`
`ajuda`""")

    return "".join(partes)