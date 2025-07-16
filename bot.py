# bot.py
from flask import Flask, request; from twilio.twiml.messaging_response import MessagingResponse; import commands, database, atexit; from apscheduler.schedulers.background import BackgroundScheduler; import traceback

app = Flask(__name__); database.init_db()

def enviar_relatorios_semanais():
    print("AGENDADOR: Executando tarefa de envio de relatórios...")
    try:
        clientes_ativos = database.get_todos_clientes_ativos()
        for cliente in clientes_ativos:
            if cliente['plano'] in ['diamante', 'trial']:
                user_id = cliente['user_id']
                relatorio = commands.gerar_relatorio_semanal(user_id)
                if relatorio: commands.enviar_mensagem_boas_vindas(user_id, relatorio)
    except Exception as e: print(f"ERRO no agendador: {e}")

scheduler = BackgroundScheduler(daemon=True, timezone='America/Sao_Paulo')
scheduler.add_job(enviar_relatorios_semanais, 'cron', day_of_week='fri', hour=18)
scheduler.start(); atexit.register(lambda: scheduler.shutdown())

@app.route("/webhook", methods=["POST"])
def webhook():
    user_id = request.form.get('From'); texto_usuario = request.form.get("Body", "").lower().strip()
    resposta_bot = MessagingResponse(); texto_resposta = ""
    try:
        cliente = database.get_cliente(user_id)
        if not cliente:
            database.ativar_cliente(user_id, 'trial', 7)
            commands.enviar_mensagem_boas_vindas(user_id, 'trial')
            return str(resposta_bot)
        elif cliente['status_assinatura'] == 'vencido':
            texto_resposta = "Olá! Sua assinatura do GerenciaCash expirou. Para reativar, acesse nosso site e escolha um novo plano."
            resposta_bot.message(texto_resposta); return str(resposta_bot)

        plano_cliente = cliente['plano']
        
        comandos_roteados = False
        if texto_usuario.startswith("orçamento"):
            if plano_cliente in ['ouro', 'diamante', 'trial']: texto_resposta = commands.gerenciar_orcamento(user_id, texto_usuario)
            else: texto_resposta = f"Desculpe, este recurso é para assinantes Ouro ou superior."
            comandos_roteados = True
        elif texto_usuario.startswith("pesquisar"):
            if plano_cliente in ['ouro', 'diamante', 'trial']: texto_resposta = commands.pesquisar_gastos(user_id, texto_usuario)
            else: texto_resposta = f"Desculpe, este recurso é para assinantes Ouro ou superior."
            comandos_roteados = True
        elif texto_usuario == "exportar":
            if plano_cliente in ['diamante', 'trial']: texto_resposta = commands.exportar_dados(user_id)
            else: texto_resposta = f"Desculpe, este recurso é exclusivo do plano Diamante."
            comandos_roteados = True
        elif texto_usuario.startswith("gasto fixo"):
            if plano_cliente in ['prata', 'ouro', 'diamante', 'trial']: texto_resposta = commands.gerenciar_gasto_fixo(user_id, texto_usuario)
            else: texto_resposta = f"Desculpe, este recurso é para assinantes Prata ou superior."
            comandos_roteados = True
        elif texto_usuario == "resumo":
            if plano_cliente in ['prata', 'ouro', 'diamante', 'trial']: texto_resposta = commands.resumo_categorias(user_id)
            else: texto_resposta = f"Desculpe, este recurso é para assinantes Prata ou superior."
            comandos_roteados = True
        elif texto_usuario.startswith("gasto"):
            if '#' in texto_usuario and plano_cliente not in ['prata', 'ouro', 'diamante', 'trial']:
                texto_resposta = f"Desculpe, o uso de categorias com # é para assinantes Prata ou superior."
            else: texto_resposta = commands.adicionar_gasto(user_id, texto_usuario)
            comandos_roteados = True
        
        if not comandos_roteados:
            if texto_usuario == "ajuda": texto_resposta = commands.mostrar_ajuda(plano_cliente)
            elif texto_usuario.startswith("saldo inicial"): texto_resposta = commands.definir_saldo_inicial(user_id, texto_usuario)
            elif texto_usuario.startswith("adicionar saldo"): texto_resposta = commands.adicionar_ao_saldo(user_id, texto_usuario)
            elif texto_usuario == "saldo" or "quanto sobrou" in texto_usuario: texto_resposta = commands.verificar_saldo_atual(user_id)
            elif texto_usuario == "listar": texto_resposta = commands.listar_gastos(user_id)
            elif texto_usuario.startswith("remover"): texto_resposta = commands.remover_gasto(user_id, texto_usuario)
            elif texto_usuario == "desfazer": texto_resposta = commands.desfazer_ultima_adicao(user_id)
            elif texto_usuario == "sim, limpar tudo": texto_resposta = commands.limpar_dados_executar(user_id)
            elif texto_usuario == "limpar tudo": texto_resposta = "⚠️ *Atenção!* Para apagar, confirme com: `sim, limpar tudo`"
            else: texto_resposta = commands.mostrar_ajuda(plano_cliente)
            
        resposta_bot.message(texto_resposta); return str(resposta_bot)
    except Exception as e:
        print(f"ERRO INESPERADO NO WEBHOOK: {e}"); print(traceback.format_exc())
        return str(MessagingResponse().message("Ops, ocorreu um erro interno. A equipe já foi notificada."))

@app.route("/webhook-kiwify", methods=['POST'])
def handle_kiwify_webhook():
    dados = request.json; print("Webhook da Kiwify recebido:", dados)
    if dados.get('event') == 'order.paid':
        cliente_info=dados.get('customer',{}); produto_info=dados.get('product',{})
        telefone=cliente_info.get('phone_number'); ddd=cliente_info.get('phone_area_code')
        if telefone and ddd:
            numero_completo=f"+55{ddd}{telefone}"; user_id=f"whatsapp:{numero_completo}"
            nome_produto=produto_info.get('name','').lower(); plano,duracao='bronze',30
            if 'prata' in nome_produto: plano = 'prata'
            elif 'ouro' in nome_produto: plano = 'ouro'
            elif 'diamante' in nome_produto: plano = 'diamante'
            if 'trimestral' in nome_produto: duracao = 90
            elif 'semestral' in nome_produto: duracao = 180
            elif 'anual' in nome_produto: duracao = 365
            database.ativar_cliente(user_id,plano,duracao); commands.enviar_mensagem_boas_vindas(user_id,plano)
    return "OK", 200

if __name__ == "__main__": app.run(debug=True, port=5000)