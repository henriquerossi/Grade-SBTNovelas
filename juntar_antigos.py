import pandas as pd
import glob
import os
import re

# Configuração de pastas
PASTA_HISTORICO = "grades" 
PASTA_SAIDA = "programas"

def padronizar_nome_arquivo(nome):
    """
    Mantém maiúsculas/minúsculas originais, remove caracteres 
    inválidos e substitui os espaços por underscores (_).
    """
    nome_limpo = str(nome)
    nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_limpo)
    nome_limpo = re.sub(r'\s+', '_', nome_limpo)
    return nome_limpo.strip('_')

# 1. Garantir que a pasta de destino exista
if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

# 2. Localizar todos os arquivos CSV antigos
arquivos = glob.glob(f"{PASTA_HISTORICO}/*.csv")

if arquivos:
    print(f"Encontrados {len(arquivos)} arquivos antigos para processar...")
    lista_dfs = []
    
    # Carrega todos os arquivos para a memória
    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo)
            lista_dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler o arquivo {arquivo}: {e}")
    
    # Juntar tudo em uma grande tabela temporária
    df_tudo = pd.concat(lista_dfs, ignore_index=True)
    
    # 3. Padronizar nomes de colunas antigos (caso varie entre maiúsculas/minúsculas)
    df_tudo = df_tudo.rename(columns={
        'dia': 'Data', 'title': 'Programa', 'episodeName': 'Episódio', 'mediaId': 'Media'
    })
    
    # 4. Limpeza de colunas indesejadas do catálogo mestre
    colunas_para_remover = ['Hora', 'horario', 'Nº do episódio', 'Episódio Nº', 'content_episode']
    for col in colunas_para_remover:
        if col in df_tudo.columns:
            df_tudo = df_tudo.drop(columns=[col])

    # 5. Converter a Data para ordenar cronologicamente antes de separar
    df_tudo['Data_Temp'] = pd.to_datetime(df_tudo['Data'], format='%d/%m/%Y', errors='coerce')
    df_tudo = df_tudo.dropna(subset=['Data_Temp']) # Remove linhas com datas corrompidas se houver
    df_tudo = df_tudo.sort_values(by='Data_Temp')

    # 6. Descobrir todos os programas únicos que existem no histórico
    programas_unicos = df_tudo['Programa'].unique()
    print(f"Total de programas/novelas diferentes detectados: {len(programas_unicos)}")

    # 7. Separar e salvar cada um no seu arquivo exclusivo
    for programa in programas_unicos:
        # Filtra apenas os dados deste programa
        df_programa = df_tudo[df_tudo['Programa'] == programa].copy()
        
        # Remove as duplicatas (mantendo a primeira exibição do capítulo)
        df_programa = df_programa.drop_duplicates(subset=['Media', 'Episódio'], keep='first')
        
        # Garante a ordenação pela data de exibição e remove a coluna temporária
        df_programa = df_programa.sort_values(by='Data_Temp', ascending=True)
        df_programa = df_programa.drop(columns=['Data_Temp'])
        
        # Gera o nome do arquivo (ex: programas/Maria_do_Bairro.csv)
        nome_arquivo = padronizar_nome_arquivo(programa)
        caminho_final = f"{PASTA_SAIDA}/{nome_arquivo}.csv"
        
        # Salva o catálogo individual deste programa
        df_programa.to_csv(caminho_final, index=False, encoding='utf-8-sig')
        print(f"-> Arquivo criado: {caminho_final} ({len(df_programa)} itens)")

    print("\nMigração concluída com sucesso! O passado está organizado.")

else:
    print(f"Erro: Nenhum arquivo .csv encontrado dentro da pasta '{PASTA_HISTORICO}'.")
