from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
import operator

# https://platform.openai.com/docs/guides/text-to-speech

class EntrevistaInput(TypedDict):
    topico: str
    entrevistado: str

class Entrevista(TypedDict):
    mensagens: Annotated[list[AnyMessage], operator.add]
    topico: str # canal compartilhado
    entrevistado: str # canal compartilhado
    temas: list[str]
    numero_maximo_de_iteracoes: int
    fontes: Annotated[list, operator.add]
    entrevista_texto: str
    introducao: str
    conclusao: str
    roteiro_final: Annotated[list[AnyMessage], operator.add]

class EntrevistaOutput(TypedDict):
    roteiro_final: str