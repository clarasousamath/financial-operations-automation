import os
import pandas as pd
from google.colab import drive, auth
from google.auth import default
import gspread
from googleapiclient.discovery import build

# ==========================================
# 1. AUTENTICAÇÃO E MAPEAMENTO DO DRIVE
# ==========================================
drive.mount('/content/drive')
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# ==========================================
# 2. DEFINIÇÃO DOS CAMINHOS DAS PASTAS
# ==========================================
caminho_a = '/content/drive/MyDrive/CASE (GRUPO BOTICÁRIO)/Case 3/Fontes/BD Fonte A'
caminho_b = '/content/drive/MyDrive/CASE (GRUPO BOTICÁRIO)/Case 3/Fontes/BD Fonte B'
caminho_c = '/content/drive/MyDrive/CASE (GRUPO BOTICÁRIO)/Case 3/Fontes/BD Fonte C'

# ==========================================
# 3. FUNÇÕES DE EXTRAÇÃO (COM PROTEÇÃO)
# ==========================================
def processar_fonte_a(pasta):
    linhas = []
    if not os.path.exists(pasta): return pd.DataFrame()
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.txt') and not arquivo.startswith('~$') and not arquivo.startswith('._'):
            with open(os.path.join(pasta, arquivo), 'r', encoding='utf-8') as f:
                for linha in f.read().strip().split('\n'):
                    if not linha.strip(): continue
                    partes = [p.strip() for p in linha.split('|')]
                    if len(partes) < 7: continue
                    deal_id = "FX-" + partes[0].split('] DEAL #')[1].strip() if "FX-" not in partes[0] else partes[0].split('] DEAL #')[1].strip()
                    op_moeda_valor = partes[1].split(' ')
                    linhas.append({
                        'Nome_Arquivo': arquivo,
                        'Deal_ID': deal_id, 'Operacao': op_moeda_valor[0], 'Moeda': op_moeda_valor[1],
                        'Valor_Chat': float(op_moeda_valor[2].replace(',', '')),
                        'Taxa_Chat': float(partes[2].replace('TX:', '').strip()),
                        'Local': partes[3], 'Banco': partes[4], 'Natureza': partes[5]
                    })
    return pd.DataFrame(linhas)

def processar_fonte_b(pasta):
    linhas = []
    if not os.path.exists(pasta): return pd.DataFrame()
    for arquivo in os.listdir(pasta):
        if (arquivo.endswith('.txt') or arquivo.endswith('.csv')) and not arquivo.startswith('~$') and not arquivo.startswith('._'):
            with open(os.path.join(pasta, arquivo), 'r', encoding='utf-8') as f:
                for linha in f.read().strip().split('\n'):
                    if not linha.strip() or "DATA_LIQ" in linha: continue
                    partes = [p.strip() for p in linha.split(';')]
                    if len(partes) < 8: continue
                    linhas.append({
                        'Nome_Arquivo': arquivo,
                        'DATA_LIQ': partes[0],
                        'CONTRATO_CAMBIO': partes[1],
                        'DEAL_ID': partes[2],
                        'MOEDA': partes[3],
                        'VALOR_MOEDA': float(partes[4]),
                        'TAXA_BANCO': float(partes[5]),
                        'VALOR_BRL_LIQUIDADO': float(partes[6]),
                        'HISTORICO': partes[7]
                    })
    return pd.DataFrame(linhas)

def processar_fonte_c(pasta):
    df_final = pd.DataFrame()
    if not os.path.exists(pasta): return df_final
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.xlsx') and not arquivo.startswith('~$') and not arquivo.startswith('._'):
            df = pd.read_excel(os.path.join(pasta, arquivo), header=1)
            df = df.dropna(how='all', axis=1)
            df = df.dropna(how='all', axis=0)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            if 'Data_Fechamento' in df.columns:
                df['Data_Fechamento'] = pd.to_datetime(df['Data_Fechamento']).dt.strftime('%d/%m/%Y')

            df.insert(0, 'Nome_Arquivo', arquivo)
            df_final = pd.concat([df_final, df], ignore_index=True)
    return df_final

# ==========================================
# 4. PROCESSAMENTO E ADIÇÃO DA COLUNA DE ORIGEM
# ==========================================
df_a = processar_fonte_a(caminho_a)
df_b = processar_fonte_b(caminho_b)
df_c = processar_fonte_c(caminho_c)

if not df_a.empty: df_a.insert(0, 'Origem', 'Fonte A - Mesa')
if not df_b.empty: df_b.insert(0, 'Origem', 'Fonte B - Extrato')
if not df_c.empty: df_c.insert(0, 'Origem', 'Fonte C - Controle')

# ==========================================
# 5. CONSOLIDAÇÃO E VALIDAÇÃO CRUZADA (CAIXA E IOF)
# ==========================================
# --- 5.1 VISÃO CONSOLIDADA ---
df_a_cons = df_a.copy().rename(columns={'Valor_Chat': 'Valor_Moeda', 'Taxa_Chat': 'Taxa'})
df_b_cons = df_b.copy().rename(columns={'DATA_LIQ': 'Data', 'DEAL_ID': 'Deal_ID', 'MOEDA': 'Moeda', 'VALOR_MOEDA': 'Valor_Moeda', 'TAXA_BANCO': 'Taxa'})
df_c_cons = df_c.copy().rename(columns={'Data_Fechamento': 'Data', 'ID_Mesa': 'Deal_ID', 'Valor_Estrangeiro': 'Valor_Moeda', 'Taxa_Acordada': 'Taxa'})

df_consolidado = pd.concat([df_a_cons, df_b_cons, df_c_cons], ignore_index=True)

if not df_consolidado.empty:
    cols_especiais = ['Origem', 'Nome_Arquivo']
    outras_cols = [c for c in df_consolidado.columns if c not in cols_especiais]
    df_consolidado = df_consolidado[cols_especiais + outras_cols]

# --- 5.2 VISÃO DE VALIDAÇÃO ---
df_validacao = pd.DataFrame()
if not df_a.empty:
    df_validacao = df_a[['Deal_ID', 'Operacao', 'Moeda', 'Valor_Chat', 'Taxa_Chat', 'Local', 'Banco', 'Natureza']].copy()

    # Cruzamento com Fonte B
    if not df_b.empty:
        df_b_val = df_b[['DEAL_ID', 'DATA_LIQ', 'CONTRATO_CAMBIO', 'TAXA_BANCO', 'VALOR_BRL_LIQUIDADO', 'HISTORICO']]
        df_validacao = pd.merge(df_validacao, df_b_val, left_on='Deal_ID', right_on='DEAL_ID', how='left')
    else:
        for col in ['DEAL_ID', 'DATA_LIQ', 'CONTRATO_CAMBIO', 'TAXA_BANCO', 'VALOR_BRL_LIQUIDADO', 'HISTORICO']: df_validacao[col] = pd.NA

    # Cruzamento com Fonte C
    if not df_c.empty:
        df_c_val = df_c[['ID_Mesa', 'Ref_ERP', 'Status_Interno', 'Taxa_Acordada']]
        df_validacao = pd.merge(df_validacao, df_c_val, left_on='Deal_ID', right_on='ID_Mesa', how='left')
    else:
        for col in ['ID_Mesa', 'Ref_ERP', 'Status_Interno', 'Taxa_Acordada']: df_validacao[col] = pd.NA

    # Tipagem numérica para os cálculos
    df_validacao['Valor_Chat'] = pd.to_numeric(df_validacao['Valor_Chat'], errors='coerce')
    df_validacao['Taxa_Chat'] = pd.to_numeric(df_validacao['Taxa_Chat'], errors='coerce')
    df_validacao['TAXA_BANCO'] = pd.to_numeric(df_validacao['TAXA_BANCO'], errors='coerce')
    df_validacao['Taxa_Acordada'] = pd.to_numeric(df_validacao['Taxa_Acordada'], errors='coerce')
    df_validacao['VALOR_BRL_LIQUIDADO'] = pd.to_numeric(df_validacao['VALOR_BRL_LIQUIDADO'], errors='coerce')

    # -------------------------------------------------------------
    # COLUNAS DE VALIDAÇÃO: PROVA REAL MATEMÁTICA (Volume x Taxas)
    # -------------------------------------------------------------
    df_validacao['Calc. BRL (Fonte A)'] = df_validacao['Valor_Chat'] * df_validacao['Taxa_Chat']
    df_validacao['Calc. BRL (Fonte B)'] = df_validacao['Valor_Chat'] * df_validacao['TAXA_BANCO']
    df_validacao['Calc. BRL (Fonte C)'] = df_validacao['Valor_Chat'] * df_validacao['Taxa_Acordada']

    # Calcula Valor BRL Base (Usando Fonte A como Negociado)
    df_validacao['Valor Negociado'] = df_validacao['Calc. BRL (Fonte A)']

    # Calcula IOF (0,38% para COMPRA, 0% para VENDA)
    is_compra = df_validacao['Operacao'].str.upper() == 'COMPRA'

    df_validacao['IOF Negociado'] = 0.0
    df_validacao.loc[is_compra, 'IOF Negociado'] = df_validacao.loc[is_compra, 'Valor Negociado'] * 0.0038

    df_validacao['IOF Liquidado'] = 0.0
    df_validacao.loc[is_compra, 'IOF Liquidado'] = df_validacao.loc[is_compra, 'VALOR_BRL_LIQUIDADO'] * 0.0038

    # Lógica financeira de Diferença (Negativo = Prejuízo / Positivo = Ganho real)
    df_validacao['Diferença (Negociado x Liquidado)'] = 0.0
    df_validacao.loc[is_compra, 'Diferença (Negociado x Liquidado)'] = df_validacao['Valor Negociado'] - df_validacao['VALOR_BRL_LIQUIDADO']
    df_validacao.loc[~is_compra, 'Diferença (Negociado x Liquidado)'] = df_validacao['VALOR_BRL_LIQUIDADO'] - df_validacao['Valor Negociado']

    # Lógica da Diferença de IOF e Total
    df_validacao['Diferença IOF'] = df_validacao['IOF Negociado'] - df_validacao['IOF Liquidado']
    df_validacao['Diferenca Total Liquidada'] = df_validacao['Diferença (Negociado x Liquidado)'] + df_validacao['Diferença IOF']

    # Renomeação final
    df_validacao = df_validacao.rename(columns={
        'Valor_Chat': 'Valor_Moeda',
        'Taxa_Chat': 'Taxa Fonte A',
        'TAXA_BANCO': 'Taxa Fonte B',
        'Taxa_Acordada': 'Taxa Fonte C',
        'DATA_LIQ': 'Data'
    })

    # Força a data de 28/08/2026 em células vazias
    df_validacao['Data'] = df_validacao['Data'].replace([pd.NA, None, 'nan', 'NaN', ''], '28/08/2026')
    df_validacao['Data'] = df_validacao['Data'].fillna('28/08/2026')

    # Ordenação expandida com as novas colunas
    colunas_ordenadas = [
        'Deal_ID', 'Operacao', 'Moeda', 'Valor_Moeda',
        'Taxa Fonte A', 'Taxa Fonte B', 'Taxa Fonte C',
        'Calc. BRL (Fonte A)', 'Calc. BRL (Fonte B)', 'Calc. BRL (Fonte C)',
        'Local', 'Banco', 'Natureza', 'Data', 'CONTRATO_CAMBIO', 'VALOR_BRL_LIQUIDADO', 'HISTORICO',
        'Ref_ERP', 'Status_Interno', 'Valor Negociado', 'IOF Negociado', 'IOF Liquidado',
        'Diferença (Negociado x Liquidado)', 'Diferença IOF', 'Diferenca Total Liquidada'
    ]
    df_validacao = df_validacao[colunas_ordenadas]

# ==========================================
# 6. SUBSTITUIÇÃO DE PONTO POR VÍRGULA E FORMATAÇÃO DE CASAS DECIMAIS
# ==========================================
def formatar_decimais(df):
    if df.empty: return df
    df_formatado = df.copy()
    for col in df_formatado.columns:
        if df_formatado[col].dtype in ['float64', 'float32']:
            # Se for taxa (3 casas decimais)
            if 'TAXA' in col.upper():
                df_formatado[col] = df_formatado[col].apply(lambda x: f"{x:.3f}".replace('.', ',') if pd.notnull(x) else "")
            # Demais valores monetários (2 casas decimais)
            else:
                df_formatado[col] = df_formatado[col].apply(lambda x: f"{x:.2f}".replace('.', ',') if pd.notnull(x) else "")
    return df_formatado.fillna("")

df_a_fmt = formatar_decimais(df_a)
df_b_fmt = formatar_decimais(df_b)
df_c_fmt = formatar_decimais(df_c)
df_cons_fmt = formatar_decimais(df_consolidado)
df_val_fmt = formatar_decimais(df_validacao)

# ==========================================
# 7. CRIAÇÃO/ATUALIZAÇÃO DO GOOGLE SHEETS
# ==========================================
nome_planilha = 'CASE 3 - Automação'
nome_pasta = 'Case 3'

query_pasta = f"name='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
resultados_pasta = drive_service.files().list(q=query_pasta, spaces='drive', fields='files(id, name)').execute()
pastas = resultados_pasta.get('files', [])
id_pasta = pastas[0]['id'] if pastas else None

query_arquivo = f"name='{nome_planilha}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
if id_pasta:
    query_arquivo += f" and '{id_pasta}' in parents"

resultados_arquivo = drive_service.files().list(q=query_arquivo, spaces='drive', fields='files(id, name)').execute()
arquivos = resultados_arquivo.get('files', [])

if arquivos:
    id_planilha = arquivos[0]['id']
    planilha = gc.open_by_key(id_planilha)
    print("Planilha existente encontrada. Atualizando os dados...")
else:
    if id_pasta:
        planilha = gc.create(nome_planilha, folder_id=id_pasta)
        print(f"Nova planilha Google Sheets criada dentro da pasta '{nome_pasta}'.")
    else:
        planilha = gc.create(nome_planilha)

try:
    planilha.batch_update({
        "requests": [{"updateSpreadsheetProperties": {"properties": {"locale": "pt_BR"}, "fields": "locale"}}]
    })
except Exception:
    pass

# ==========================================
# 8. GRAVAÇÃO DAS ABAS (USER_ENTERED)
# ==========================================
def atualizar_aba(planilha, nome_aba, dataframe):
    if dataframe.empty: return
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows="100", cols="20")

    aba.clear()
    df_str = dataframe.astype(str)

    df_str = df_str.replace(['nan', 'NaN', 'NaT', 'None'], '')
    dados = [df_str.columns.values.tolist()] + df_str.values.tolist()

    try:
        aba.update(range_name='A1', values=dados, value_input_option='USER_ENTERED')
    except TypeError:
        aba.update('A1', dados, value_input_option='USER_ENTERED')

atualizar_aba(planilha, 'Fonte_A', df_a_fmt)
atualizar_aba(planilha, 'Fonte_B', df_b_fmt)
atualizar_aba(planilha, 'Fonte_C', df_c_fmt)
atualizar_aba(planilha, 'Consolidado', df_cons_fmt)
atualizar_aba(planilha, 'Validacao', df_val_fmt)

print(f"\n Automação Concluída! Acesse seu Google Planilhas atualizado aqui: {planilha.url}")
