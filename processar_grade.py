import pandas as pd
import requests
import os
from datetime import datetime

# URL do JSON do canal (Substitua abaixo)
URL_JSON = "https://bridge.evrideo.tv/SBTEPG?ChannelUID=novelas&DurationHours=168"

try:
    # 1. Criar a pasta 'historico' se ela não existir
    if not os.path.exists('grades'):
        os.makedirs('grades')

    response = requests.get(URL_JSON)
    dados = response.json()
    df = pd.DataFrame(dados)

    # 2. Extrair 'content_episode' de 'macros'
    df_macros = pd.json_normalize(df['macros'])
    df['content_episode'] = df_macros['content_episode']

    # 3. Tratar Datas e Horários (Fuso de Brasília)
    dt_series = pd.to_datetime(df['startTime'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    df['dia'] = dt_series.dt.strftime('%d/%m/%Y')
    df['horario'] = dt_series.dt.strftime('%H:%M')

    # 4. Selecionar colunas
    colunas_finais = ['dia', 'horario', 'title', 'episodeName', 'content_episode', 'mediaId']
    df_resultado = df[colunas_finais]

    # Renomear para ficar "bonito" no CSV
    df_resultado = df_resultado.rename(columns={
        'dia': 'Data',
        'horario': 'Hora',
        'title': 'Programa',
        'episodeName': 'Episódio',
        'content_episode': 'Nº do episódio',
        'mediaId': 'Media'
    })

    # 5. Nome do arquivo dentro da pasta 'historico'
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    nome_arquivo = f"grades/grade_{data_hoje}.csv"

    # 6. Salvar CSV
    df_resultado.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
    print(f"Sucesso: Arquivo {nome_arquivo} criado com sucesso!")

except Exception as e:
    print(f"Erro no processamento: {e}")
