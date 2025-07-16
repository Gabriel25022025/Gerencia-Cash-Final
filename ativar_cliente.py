# ativar_cliente.py

import sys
import database
import commands

def main():
    """
    Script para ativar um novo cliente em um plano específico.
    Uso: python ativar_cliente.py <numero_whatsapp> <plano> [duracao_dias]
    Exemplos:
    python ativar_cliente.py +5511999998888 ouro 30
    python ativar_cliente.py +5511999998888 trial
    """
    if len(sys.argv) < 2:
        print("Erro: Faltam argumentos.")
        print("Uso: python ativar_cliente.py <numero_whatsapp> <plano> [duracao_em_dias]")
        print("Planos válidos: trial, bronze, prata, ouro, diamante")
        return

    numero_whatsapp = sys.argv[1]
    # Se o plano não for fornecido, assume 'trial'
    plano = sys.argv[2].lower() if len(sys.argv) > 2 else 'trial'
    
    # Define a duração padrão baseada no plano
    if plano == 'trial':
        duracao_dias = 7
    elif len(sys.argv) > 3:
        duracao_dias = int(sys.argv[3])
    else:
        duracao_dias = 30 # Padrão de 30 dias para planos pagos

    planos_validos = ['trial', 'bronze', 'prata', 'ouro', 'diamante']
    if plano not in planos_validos:
        print(f"Erro: Plano '{plano}' é inválido. Use um dos seguintes: {planos_validos}")
        return

    user_id = f"whatsapp:{numero_whatsapp}"

    print(f"Ativando cliente: {user_id} no plano {plano} por {duracao_dias} dias...")
    database.ativar_cliente(user_id, plano, duracao_dias)
    commands.enviar_mensagem_boas_vindas(user_id, plano)
    print("\nProcesso concluído!")

if __name__ == "__main__":
    main()