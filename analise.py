import json
import os
from collections import defaultdict

def formatar_tamanho_arquivo(tamanho_em_bytes):
    """Formata um tamanho em bytes para KB, MB, GB, etc."""
    if tamanho_em_bytes < 1024:
        return f"{tamanho_em_bytes} Bytes"
    elif tamanho_em_bytes < 1024**2:
        return f"{tamanho_em_bytes/1024:.2f} KB"
    elif tamanho_em_bytes < 1024**3:
        return f"{tamanho_em_bytes/1024**2:.2f} MB"
    else:
        return f"{tamanho_em_bytes/1024**3:.2f} GB"

def mapear_estrutura_recursivamente(objeto, estrutura_mapeada, caminho_atual=""):
    """Navega recursivamente para mapear a estrutura hierárquica completa do JSON."""
    if isinstance(objeto, dict):
        for chave, valor in objeto.items():
            caminho_completo = f"{caminho_atual}.{chave}" if caminho_atual else chave
            # --- ALTERAÇÃO: Adiciona na lista apenas se ainda não existir ---
            if caminho_completo not in estrutura_mapeada:
                estrutura_mapeada.append(caminho_completo)
            mapear_estrutura_recursivamente(valor, estrutura_mapeada, caminho_completo)
    elif isinstance(objeto, list):
        caminho_da_lista = f"{caminho_atual}[]"
        for item in objeto:
            mapear_estrutura_recursivamente(item, estrutura_mapeada, caminho_da_lista)

def imprimir_arvore_de_parametros(caminhos):
    """Converte uma lista de caminhos de parâmetros em uma árvore visual."""
    arvore = {}
    # --- ALTERAÇÃO: Itera sobre os caminhos na ordem em que foram encontrados (sem sorted()) ---
    for caminho in caminhos:
        # Usa um substituto temporário para facilitar o split
        partes = caminho.replace("[]", ".[LISTA]").split('.')
        galho_atual = arvore
        for parte in partes:
            # setdefault mantém a ordem de inserção em dicionários (Python 3.7+)
            galho_atual = galho_atual.setdefault(parte.replace("[LISTA]", "[] (Lista de Objetos)"), {})

    def _imprimir_galhos(dicionario, prefixo=""):
        galhos = list(dicionario.keys())
        for i, galho in enumerate(galhos):
            e_ultimo = (i == len(galhos) - 1)
            conector = "└── " if e_ultimo else "├── "
            print(f"{prefixo}{conector}{galho}")
            
            novo_prefixo = prefixo + ("    " if e_ultimo else "│   ")
            _imprimir_galhos(dicionario[galho], novo_prefixo)
            
    _imprimir_galhos(arvore)


def contar_valores_vazios_recursivamente(objeto, contador):
    """Navega recursivamente em um objeto para contar chaves com valores vazios/nulos."""
    if isinstance(objeto, dict):
        for chave, valor in objeto.items():
            if valor is None or valor == "" or valor == [] or valor == {}:
                contador[chave] += 1
            contar_valores_vazios_recursivamente(valor, contador)
    elif isinstance(objeto, list):
        for item in objeto:
            contar_valores_vazios_recursivamente(item, contador)

def analisar_parametros_jsonl(caminho_arquivo):
    """
    Analisa um arquivo .jsonl, mapeia a estrutura hierárquica dos parâmetros,
    conta as linhas, identifica parâmetros vazios e mostra o tamanho do arquivo.
    """
    # --- ALTERAÇÃO: Usa uma lista para manter a ordem de descoberta ---
    mapeamento_da_estrutura = []
    total_linhas = 0
    linhas_validas = 0
    linhas_em_branco = 0
    linhas_invalidas = 0
    contagem_parametros_vazios = defaultdict(int)

    print(f"🔎 Analisando o arquivo: {caminho_arquivo}...")

    try:
        tamanho_do_arquivo_bytes = os.path.getsize(caminho_arquivo)
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for total_linhas, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha:
                    linhas_em_branco += 1
                    continue
                try:
                    dados = json.loads(linha)
                    linhas_validas += 1
                    
                    mapear_estrutura_recursivamente(dados, mapeamento_da_estrutura)
                    contar_valores_vazios_recursivamente(dados, contagem_parametros_vazios)
                except json.JSONDecodeError:
                    print(f"⚠️ Aviso: A linha {total_linhas} não é um JSON válido e foi ignorada.")
                    linhas_invalidas += 1

    except FileNotFoundError:
        print(f"❌ Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
        return

    # 1. Relatório de Estrutura
    print("\n" + "="*40)
    print("🌳 Estrutura de Parâmetros Identificada (na ordem de aparição):")
    if mapeamento_da_estrutura:
        imprimir_arvore_de_parametros(mapeamento_da_estrutura)
    else:
        print("🤷 Nenhuma estrutura de parâmetros foi encontrada no arquivo.")
    print("="*40)

    # 2. Relatório de Estatísticas do Arquivo
    print("\n" + "="*40)
    print("📊 Estatísticas do Arquivo:")
    print(f"- Tamanho do arquivo: {formatar_tamanho_arquivo(tamanho_do_arquivo_bytes)}")
    print(f"- Total de linhas lidas: {total_linhas}")
    print(f"- Linhas com JSON válido (registros): {linhas_validas}")
    print(f"- Linhas em branco: {linhas_em_branco}")
    print(f"- Linhas com JSON inválido: {linhas_invalidas}")
    print("="*40)

    # 3. Relatório de Parâmetros Vazios
    print("\n" + "="*40)
    print("🔎 Análise de Parâmetros Vazios/Nulos (todos os níveis):")
    if contagem_parametros_vazios:
        print("(Contagem de vezes que um parâmetro apareceu com valor nulo, \"\", [] ou {})")
        # A contagem de vazios continua ordenada alfabeticamente para facilitar a busca
        for parametro in sorted(contagem_parametros_vazios.keys()):
            contagem = contagem_parametros_vazios[parametro]
            print(f"- Parâmetro '{parametro}': {contagem} vez(es) sem valor")
    else:
        print("✅ Nenhum parâmetro com valor vazio ou nulo foi encontrado.")
    print("="*40)

if __name__ == "__main__":
    nome_do_arquivo = input("Digite o nome do seu arquivo .jsonl (ex: dados.jsonl): ")
    analisar_parametros_jsonl(nome_do_arquivo)