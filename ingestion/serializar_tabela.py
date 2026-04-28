
def serializar_tabela(tabela: list[list]) -> str:
    if not tabela or len(tabela) < 2:
        return ""

    headers = [str(h).replace("\n", " ").strip() if h else "" for h in tabela[0]]
    linhas_texto = []

    for row in tabela[1:]:
        pares = []
        for header, cell in zip(headers, row):
            if cell and str(cell).strip():
                valor = str(cell).replace("\n", " ").strip()
                pares.append(f"{header}: {valor}")
        if pares:
            linhas_texto.append(" | ".join(pares))

    return "\n".join(linhas_texto)
