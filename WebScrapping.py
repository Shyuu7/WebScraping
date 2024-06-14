import sqlite3
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração do Selenium
driver = webdriver.Chrome()
url = 'https://www.turismo.gov.br/agenda-eventos/views/calendario.php'
driver.get(url)

# Função para criar tabelas
def criar_tabela(nome_tabela, query):
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('EventosDB.db')
        c = conn.cursor()

        # Verificar se a tabela já existe
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{nome_tabela}';")
        if c.fetchone():
            print(f"\nTabela {nome_tabela} já existe.")
            print("\n=====================================================================")
        else:
            # Criar a tabela
            c.execute(query)
            print(f"\nTabela {nome_tabela} criada com sucesso!")
            print("\n=====================================================================")

        # Fechar a conexão com o banco de dados
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"\nErro ao criar a tabela {nome_tabela}: {e}")

# Criando a tabela Eventos
query = ('''
        CREATE TABLE IF NOT EXISTS Eventos (
            evento_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR (100) NOT NULL,
            tipo TEXT
        )
    ''')
criar_tabela('Eventos', query)

# Criando a tabela DadosEventos
query = ('''
        CREATE TABLE IF NOT EXISTS DadosEventos (
            dados_evento_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER,
            descricao TEXT,
            categoria TEXT,
            data_inicio DATE,
            data_final DATE,
            localizacao TEXT,
            ar_livre BOOLEAN,
            FOREIGN KEY(evento_id) REFERENCES Eventos(evento_id)
        )
    ''')
criar_tabela('DadosEventos', query)

# Criando a tabela Metadados
query = ('''
        CREATE TABLE IF NOT EXISTS Metadados (
            metadado_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento_id INTEGER,
            metadado TEXT,
            FOREIGN KEY(evento_id) REFERENCES Eventos(evento_id)
        )
    ''')
criar_tabela('Metadados', query)

# Função para verificar se uma tabela está vazia
def tabela_vazia(nome_tabela):
    conn = sqlite3.connect('EventosDB.db')
    c = conn.cursor()
    c.execute(f'SELECT COUNT(*) FROM {nome_tabela}')
    count = c.fetchone()[0]
    conn.close()
    return count == 0

# Dicionário de equivalência de meses
meses = {
    "Jan": "01",
    "Fev": "02",
    "Mar": "03",
    "Abr": "04",
    "Mai": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Set": "09",
    "Out": "10",
    "Nov": "11",
    "Dez": "12"
}

# Função para converter a data para o formato YYYY-MM-DD
def converter_data(data):
    dia, mes, ano = data.split()
    ano = "20" + ano  
    mes_num = meses[mes]
    data_formatada = f"{ano}-{mes_num}-{dia.zfill(2)}"
    return data_formatada

# Verificar se as tabelas estão vazias
if tabela_vazia('Eventos') or tabela_vazia('DadosEventos') or tabela_vazia('Metadados'):
    print("Uma ou mais tabelas estão vazias. Iniciando extração de dados...")

    # Função para extrair os detalhes do evento
    def extrair_detalhes(html):
        soup = BeautifulSoup(html, 'html.parser')
        detalhe_container = soup.find('div', id='detalhe-container')
        if not detalhe_container:
            return None, None, None

        # Extraindo os detalhes
        sobre = ""
        sobre_tag = detalhe_container.find('p', string='Sobre:')
        if sobre_tag:
            sobre = sobre_tag.find_next('p').text.strip()

        # Extraindo o tipo de evento
        tipo = ""
        tipo_tag = detalhe_container.find('span', string=re.compile(r'\s*Tipo:\s*'))
        if tipo_tag:
            tipo = tipo_tag.next_sibling.text.strip()

        metadado = detalhe_container.find('div', class_='detalhe')

        return sobre, tipo, metadado

    # Extraindo informações da página inicial
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    div_principal = soup.find_all('div', class_='new-card-content')

    # Lista para armazenar os eventos
    eventos = []

    for div in div_principal:
        # Extraindo a categoria
        categoria = div.find('div', class_='categoria').text.strip()

        # Extraindo a data
        data_div = div.find('div', class_='data')
        dia = data_div.find('span', class_='dia').text.strip()
        mes = data_div.find('span', class_='mes').text.strip()
        data_final_texto = data_div.find('span', class_='final').text.strip()
        data_inicio = converter_data(f"{dia} {mes} 24")
        data_final = converter_data(data_final_texto)

        # Extraindo o nome do evento
        nome = div.find('span', class_='nome').text.strip().lower()
        # Formatação do nome para primeira letra de cada palavra em maiúsculo
        nome = ' '.join(word[0].upper() + word[1:] for word in nome.split())

        # Extraindo a localização
        localizacao = div.find('span', class_='localizacao').text.strip()

        # Adicionando os detalhes do evento na lista de eventos
        eventos.append((categoria, nome, localizacao, data_inicio, data_final))

    # Clicando em cada div com a classe new-card e extraindo os detalhes
    new_cards = driver.find_elements(By.CLASS_NAME, 'new-card')
    for i, card in enumerate(new_cards):
        # Scroll para o elemento
        actions = ActionChains(driver)
        actions.move_to_element(card).perform()

        # Fecha o overlay se estiver presente
        try:
            overlay = driver.find_element(By.ID, 'overlay')
            if overlay.is_displayed():
                driver.execute_script("arguments[0].click();", overlay)
        except:
            pass

        # Clique no card
        card.click()

        # Espera pelo detalhe container aparecer
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, 'detalhe-container'))
        )

        # Extrai os detalhes
        detalhe_html = driver.page_source
        sobre, tipo, metadado = extrair_detalhes(detalhe_html)

        # Determina se é ao ar livre
        ar_livre = True if tipo == "Feira/Exposição/Mostra" else False

        # Conecta ao banco de dados
        conn = sqlite3.connect('EventosDB.db')
        c = conn.cursor()

        # Insere os dados no banco de dados
        c.execute('INSERT INTO Eventos (nome, tipo) VALUES (?, ?)', (eventos[i][1], tipo))
        evento_id = c.lastrowid

        c.execute('INSERT INTO DadosEventos (evento_id, data_inicio, data_final, localizacao, ar_livre, descricao, categoria) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (evento_id, eventos[i][3], eventos[i][4], eventos[i][2], ar_livre, sobre, eventos[i][0]))

        metadado_html = metadado.prettify()
        c.execute('INSERT INTO Metadados (evento_id, metadado) VALUES (?, ?)',
                  (evento_id, metadado_html))

        conn.commit()
        conn.close()

        # Clicar fora da div para fechá-la
        body = driver.find_element(By.TAG_NAME, 'body')
        actions.move_to_element(body).click().perform()

else:
    print("Todas as tabelas já contêm dados. Extração de dados não necessária.")

# Fechando o navegador
driver.quit()

# Consultas SQL e impressão dos resultados
def executar_consulta(query):
    conn = sqlite3.connect('EventosDB.db')
    c = conn.cursor()
    c.execute(query)
    resultados = c.fetchall()
    conn.close()
    return resultados

# 1. Mostrar todos os eventos com suas datas, localização, e tipo de evento.
query1 = '''
SELECT e.nome, d.data_inicio, d.data_final, d.localizacao, e.tipo 
FROM Eventos e
JOIN DadosEventos d ON e.evento_id = d.evento_id
'''
resultados1 = executar_consulta(query1)
print("\nTodos os eventos com suas datas, localização, e tipo de evento:")
for linha in resultados1:
    print(linha)
print("\n=====================================================================")

# 2. Mostrar os dados dos 2 eventos mais próximos de iniciar.
query2 = '''
SELECT e.nome, d.data_inicio, d.data_final, d.localizacao, e.tipo 
FROM Eventos e
JOIN DadosEventos d ON e.evento_id = d.evento_id
ORDER BY ABS(julianday('now') - julianday(d.data_inicio)) ASC
LIMIT 2;
'''
resultados2 = executar_consulta(query2)
print("\nOs dados dos 2 eventos mais próximos de iniciar:")
for linha in resultados2:
    print(linha)
print("\n=====================================================================")

# 3. Mostrar os eventos que acontecem no Rio de Janeiro.
query3 = '''
SELECT e.nome, d.data_inicio, d.data_final, d.localizacao, e.tipo 
FROM Eventos e
JOIN DadosEventos d ON e.evento_id = d.evento_id
WHERE d.localizacao LIKE '%/RJ%'
'''
resultados3 = executar_consulta(query3)
print("\nEventos que acontecem no RJ:")
for linha in resultados3:
    print(linha)
print("\n=====================================================================")

# 4. Mostrar todos os eventos que são ao ar livre.
query4 = '''
SELECT e.nome, d.data_inicio, d.data_final, d.localizacao, e.tipo 
FROM Eventos e
JOIN DadosEventos d ON e.evento_id = d.evento_id
WHERE d.ar_livre = 1
'''
resultados4 = executar_consulta(query4)
print("\nTodos os eventos que são ao ar livre:")
for linha in resultados4:
    print(linha)
print("\n=====================================================================")

# 5. Mostrar todos os Metadados por evento.
query5 = '''
SELECT e.nome, m.metadado 
FROM Eventos e
JOIN Metadados m ON e.evento_id = m.evento_id
'''
resultados5 = executar_consulta(query5)
print("Todos os Metadados por evento:")
for linha in resultados5:
    print(linha)
print("\n=====================================================================")