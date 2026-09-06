import pandas as pd
import requests
import os
import re
from datetime import datetime

# CONFIGURAÇÃO DO CANAL (Insira a URL correspondente)
URL_JSON = "https://d31l2nn7dlh4li.cloudfront.net/amg00527/epg_deliveries/amgplt0764/amg00527c9/amg00527c9.json"

def padronizar_nome_arquivo(nome):
    """
    Mantém maiúsculas/minúsculas originais, remove caracteres 
    inválidos e substitui os espaços por underscores (_).
    """
    nome_limpo = str(nome)
    nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_limpo)
    nome_limpo = re.sub(r'\s+', '_', nome_limpo)
    return nome_limpo.strip('_')

try:
    # 1. Garantir que as pastas de estrutura existem
    if not os.path.exists('grades'):
        os.makedirs('grades')
    if not os.path.exists('programas'):
        os.makedirs('programas')

    # 2. Captura dos novos dados da API
    response = requests.get(URL_JSON)
    df = pd.DataFrame(response.json())

    # 3. Tratamento de fuso horário e colunas primárias
    df_macros = pd.json_normalize(df['macros'])
    df['content_episode'] = df_macros['content_episode']
    
    dt_series = pd.to_datetime(df['startTime'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    df['Data'] = dt_series.dt.strftime('%d/%m/%Y')
    df['Hora'] = dt_series.dt.strftime('%H:%M')

    df = df.rename(columns={'title': 'Programa', 'episodeName': 'Episódio', 'mediaId': 'Media'})

    # --- PASSO A: SALVAR BACKUP DIÁRIO BRUTO ---
    # Guarda o histórico completo com Hora e Nº do episódio original na pasta 'grades/'
    df_backup = df[['Data', 'Hora', 'Programa', 'Episódio', 'content_episode', 'Media']].copy()
    df_backup = df_backup.rename(columns={'content_episode': 'Nº do episódio'})
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    df_backup.to_csv(f"grades/grade_{data_hoje}.csv", index=False, encoding='utf-8-sig')

    # --- PASSO B: DISTRIBUIR NOVOS CAPÍTULOS NOS CATÁLOGOS ---
    # Seleciona apenas as colunas que vão para os arquivos individuais (sem Hora)
    df_novo_item = df[['Data', 'Programa', 'Episódio', 'Media']].copy()
    programas_na_grade = df_novo_item['Programa'].unique()

    for programa in programas_na_grade:
        # Filtra os dados deste programa na semana atual
        df_programa_novo = df_novo_item[df_novo_item['Programa'] == programa]
        
        # Define o caminho do arquivo (ex: programas/Maria_do_Bairro.csv)
        nome_padrao = padronizar_nome_arquivo(programa)
        caminho_arquivo = f"programas/{nome_padrao}.csv"
        
        # Se o arquivo do programa já existe, combina o antigo com o novo
        if os.path.exists(caminho_arquivo):
            df_mestre_programa = pd.read_csv(caminho_arquivo)
            df_final_programa = pd.concat([df_mestre_programa, df_programa_novo], ignore_index=True)
        else:
            df_final_programa = df_programa_novo

        # Remove as duplicatas (evita re-adicionar o mesmo capítulo/mídia)
        df_final_programa = df_final_programa.drop_duplicates(subset=['Media', 'Episódio'], keep='first')

        # Ordena cronologicamente pela data em que foi exibido
        df_final_programa['Data_Temp'] = pd.to_datetime(df_final_programa['Data'], format='%d/%m/%Y', errors='coerce')
        df_final_programa = df_final_programa.sort_values(by='Data_Temp', ascending=True)
        df_final_programa = df_final_programa.drop(columns=['Data_Temp'])

        # Salva ou atualiza o CSV exclusivo daquele programa
        df_final_programa.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')

    print("Processamento concluído: Backups criados e arquivos por programa atualizados!")

except Exception as e:
    print(f"Erro no processamento: {e}")
