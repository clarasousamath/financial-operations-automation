# Case 3 — IA Aplicada em Resultado | Operações Financeiras

## 📌 Sobre o projeto

Este projeto foi desenvolvido como parte do processo seletivo para a posição de **Analista de Operações Financeiras I** do Grupo Boticário.

O desafio consiste em automatizar a conciliação de **8 operações de câmbio** realizadas pela mesa de operações em 28/08/2026, confrontando diferentes fontes de informação utilizadas pela Tesouraria.

O objetivo foi transformar dados brutos e descentralizados em uma estrutura única de validação, permitindo:

* conciliar operações entre diferentes fontes;
* validar valores e taxas negociadas e liquidadas;
* aplicar automaticamente as regras de IOF;
* identificar divergências financeiras;
* calcular o impacto líquido no caixa;
* estruturar informações para análise de performance dos bancos;
* reduzir atividades manuais e riscos operacionais;
* propor uma arquitetura de automação para o processo.

---

## 🎯 Contexto do negócio

A empresa fictícia **Grande Belleza Cosméticos S.A. (GB)** realiza operações de comércio exterior, importando insumos e exportando produtos acabados.

Essas operações envolvem diferentes moedas, países e instituições financeiras, tornando a conciliação uma atividade crítica para a Tesouraria.

Para o case, foram disponibilizadas três fontes:

| Fonte       | Descrição                 | Característica      |
| ----------- | ------------------------- | ------------------- |
| **Fonte A** | Chat da Mesa de Operações | Dados da negociação |
| **Fonte B** | Extrato bancário          | Dados da liquidação |
| **Fonte C** | Controle da Tesouraria    | Registro interno    |

O principal desafio é garantir que uma mesma operação esteja consistente nas diferentes fontes.

---

## 🔎 Problema identificado

O processo manual de conciliação pode exigir que o analista:

1. abra diferentes arquivos;
2. localize cada operação;
3. copie informações entre bases;
4. compare taxas;
5. valide valores;
6. confira contratos;
7. calcule IOF;
8. identifique divergências;
9. consolide os resultados;
10. prepare as informações para análise.

Esse fluxo aumenta o risco de:

* erros de digitação;
* divergências não identificadas;
* cálculos incorretos;
* perda de rastreabilidade;
* dependência de controles paralelos;
* consumo excessivo de tempo operacional.

A proposta deste projeto é utilizar **Python para automatizar essas etapas**, mantendo o analista focado na análise e na tomada de decisão.

---

# 🧠 Abordagem da solução

A solução foi estruturada em etapas:

```text
Fontes de dados
      ↓
Extração automática
      ↓
Padronização
      ↓
Consolidação
      ↓
Cruzamento pelo Deal_ID
      ↓
Validação financeira
      ↓
Aplicação do IOF
      ↓
Identificação de divergências
      ↓
Resultado estruturado
      ↓
Google Sheets
```

---

## ⚙️ 1. Extração dos dados

O código realiza a leitura automática dos arquivos armazenados no Google Drive.

São processadas três fontes distintas:

### Fonte A — Mesa de Operações

Os arquivos `.txt` são interpretados para extrair informações como:

* Deal ID;
* operação;
* moeda;
* valor;
* taxa;
* local;
* banco;
* natureza.

### Fonte B — Extrato bancário

São extraídos:

* data de liquidação;
* contrato de câmbio;
* Deal ID;
* moeda;
* valor em moeda estrangeira;
* taxa bancária;
* valor liquidado em BRL;
* histórico.

### Fonte C — Controle da Tesouraria

Os arquivos Excel são lidos e padronizados automaticamente, considerando informações como:

* Deal ID;
* referência no ERP;
* status interno;
* taxa acordada;
* valor em moeda estrangeira;
* data de fechamento.

---

# 🔗 2. Consolidação das fontes

Após a extração, os dados são padronizados para permitir uma visão consolidada das operações.

As diferentes nomenclaturas utilizadas pelas fontes são normalizadas.

Por exemplo:

```text
Valor_Chat
VALOR_MOEDA
Valor_Estrangeiro
```

passam a representar uma mesma informação conceitual:

```text
Valor_Moeda
```

O mesmo processo é aplicado às taxas, datas e identificadores das operações.

---

# 🔍 3. Conciliação das operações

O **Deal_ID** é utilizado como principal chave de relacionamento entre as fontes.

A partir dele, a solução realiza o cruzamento entre:

```text
Mesa de Operações
        ↕
Extrato Bancário
        ↕
Controle Interno
```

Isso permite comparar automaticamente as informações registradas nos diferentes sistemas/controles.

---

# 💰 4. Validação financeira

Além de simplesmente comparar os valores registrados, a solução realiza uma validação matemática.

O valor em reais é recalculado utilizando:

```text
Valor em moeda estrangeira × Taxa de câmbio
```

São calculados:

* BRL pela taxa da Mesa;
* BRL pela taxa do Banco;
* BRL pela taxa do Controle Interno.

Isso cria uma segunda camada de validação, permitindo verificar não apenas se os registros são iguais, mas também se os valores fazem sentido matematicamente.

---

# 🧾 5. Aplicação automática do IOF

O case determina:

| Tipo de operação       |       IOF |
| ---------------------- | --------: |
| Compra FX / Importação | **0,38%** |
| Venda FX / Exportação  |    **0%** |

A regra foi incorporada diretamente à lógica do processamento.

Para operações de compra:

```text
IOF = Valor em BRL × 0,0038
```

Para operações de venda:

```text
IOF = R$ 0,00
```

Dessa forma, o cálculo deixa de depender de uma operação manual do analista.

---

# 📊 6. Impacto financeiro

A solução calcula a diferença entre o valor negociado e o valor efetivamente liquidado.

Para operações de **compra**:

```text
Diferença = Valor Negociado − Valor Liquidado
```

Para operações de **venda**:

```text
Diferença = Valor Liquidado − Valor Negociado
```

Também é calculada a diferença de IOF:

```text
Diferença IOF =
IOF Negociado − IOF Liquidado
```

E, finalmente:

```text
Diferença Total Liquidada =
Diferença Cambial + Diferença de IOF
```

Essa estrutura permite chegar ao impacto financeiro líquido das operações.

---

# 🏦 7. Análise das instituições financeiras

A estrutura criada também permite comparar as taxas praticadas pelas instituições financeiras.

A análise pode ser segmentada por:

* banco;
* moeda;
* operação;
* compra;
* venda;
* taxa negociada;
* volume financeiro.

Assim, é possível avaliar a performance comercial dos bancos em:

```text
Compra USD
Compra EUR
Venda USD
Venda EUR
```

O objetivo não é apenas identificar a menor ou maior taxa, mas relacionar **taxa + volume + tipo de operação**, permitindo uma análise mais adequada da performance financeira.

---

# 🤖 8. Fluxo de automação desenvolvido

A automação realizada neste projeto segue o fluxo abaixo:

                 ┌──────────────────────┐
                 │ Arquivos no Drive    │
                 │ Fonte A, B e C       │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Leitura automática   │
                 │ TXT e Excel          │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Extração e           │
                 │ padronização         │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Consolidação das     │
                 │ três fontes          │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Cruzamento pelo     │
                 │ Deal_ID              │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Validação de valores│
                 │ e taxas              │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Aplicação do IOF e  │
                 │ cálculo das diferenças│
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Identificação das   │
                 │ divergências         │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Atualização do       │
                 │ Google Sheets        │
                 └──────────────────────┘

O fluxo executado pelo código começa com os arquivos disponibilizados no Google Drive e termina com a geração das bases consolidadas e da aba de validação no Google Sheets.

Neste projeto, a automação foi realizada por meio de regras determinísticas em Python. Não foi implementado um modelo de IA para interpretar documentos ou chats. A inteligência aplicada está relacionada à estruturação do processo, à padronização dos dados e à aplicação automática das regras financeiras definidas para o case.

---

# 🛠️ Tecnologias utilizadas

* **Python**
* **Pandas** — manipulação e transformação dos dados
* **Google Colab** — ambiente de execução
* **Google Drive API** — acesso e organização dos arquivos
* **Google Sheets API**
* **gspread** — integração Python ↔ Google Sheets
* **Google Authentication**
* **OpenPyXL / Pandas Excel** — leitura dos arquivos Excel

---

# 🚀 Execução

O projeto foi desenvolvido para execução no **Google Colab**.

### 1. Montar o Google Drive

O código realiza a montagem do Drive:

```python
drive.mount('/content/drive')
```

### 2. Autenticar as APIs Google

```python
auth.authenticate_user()
```

As credenciais são utilizadas para acessar o Google Drive e atualizar o Google Sheets.

### 3. Definir as fontes

Os caminhos das três fontes são configurados no código:

```python
caminho_a = '.../BD Fonte A'
caminho_b = '.../BD Fonte B'
caminho_c = '.../BD Fonte C'
```

### 4. Executar o processamento

O script:

1. lê os arquivos;
2. transforma os dados;
3. consolida as fontes;
4. realiza os cruzamentos;
5. calcula as validações;
6. aplica o IOF;
7. calcula as diferenças;
8. atualiza automaticamente o Google Sheets.

---

# 📈 Resultado da automação

Ao final do processamento, o Google Sheets é estruturado automaticamente com as seguintes abas:

```text
Fonte_A
Fonte_B
Fonte_C
Consolidado
Validacao
```

A aba **Validacao** concentra as informações necessárias para análise das operações e apresenta os principais cálculos financeiros derivados do cruzamento das fontes.

---

# 💡 Principais ganhos esperados

A solução busca gerar ganhos em quatro dimensões:

### Eficiência operacional

Redução do trabalho manual de copiar, colar e comparar informações.

### Confiabilidade

Aplicação padronizada das regras de validação e cálculo.

### Rastreabilidade

Manutenção da origem dos dados e possibilidade de identificar a fonte de cada informação.

### Escalabilidade

O mesmo processo pode ser executado para um volume maior de operações sem aumentar proporcionalmente o esforço operacional.

---

# 🎯 Conclusão

O projeto demonstra como **automação, análise financeira e inteligência artificial podem ser combinadas para transformar uma atividade operacional de Tesouraria em um processo mais eficiente, controlado e escalável**.

Mais do que automatizar cálculos, a proposta é mudar o papel do analista:

```text
ANTES

Analista
   ↓
Busca dados
   ↓
Copia informações
   ↓
Confere planilhas
   ↓
Calcula manualmente
   ↓
Procura divergências


DEPOIS

Automação
   ↓
Extrai dados
   ↓
Padroniza
   ↓
Concilia
   ↓
Aplica regras
   ↓
Identifica exceções
   ↓
        Analista
           ↓
     Analisa e decide
```

A automação, portanto, não elimina a atuação do profissional de Operações Financeiras. **Ela desloca o tempo do analista de tarefas repetitivas para atividades de maior valor, como análise, gestão de exceções, relacionamento com bancos e tomada de decisão.**
