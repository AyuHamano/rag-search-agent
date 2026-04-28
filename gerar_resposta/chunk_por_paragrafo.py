
import re

def chunk_por_paragrafo(texto: str, chunk_size: int, overlap: int) -> list[str]:

    paragrafos = re.split(r'\n\s*\n|\n(?=\d+\.\s)', texto)
    paragrafos = [p.strip() for p in paragrafos if p.strip()]

    chunks = []
    chunk_atual = ""

    for paragrafo in paragrafos:
        if len(paragrafo) > chunk_size:
            sentencas = re.split(r'(?<=[.;])\s+', paragrafo)
            for s in sentencas:
                if len(chunk_atual) + len(s) <= chunk_size:
                    chunk_atual += " " + s
                else:
                    if chunk_atual:
                        chunks.append(chunk_atual.strip())
                    chunk_atual = s
        else:
            if len(chunk_atual) + len(paragrafo) <= chunk_size:
                chunk_atual += "\n" + paragrafo
            else:
                if chunk_atual:
                    chunks.append(chunk_atual.strip())
                # Overlap: reutilizar final do chunk anterior
                chunk_atual = chunk_atual[-overlap:] + "\n" + paragrafo

    if chunk_atual.strip():
        chunks.append(chunk_atual.strip())

    return chunks