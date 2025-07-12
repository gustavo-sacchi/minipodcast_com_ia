from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import WikipediaLoader
from pydantic import BaseModel, Field

from src.state_app import EntrevistaInput, Entrevista, EntrevistaOutput

from langchain_core.messages import SystemMessage, AIMessage


from langgraph.graph import StateGraph, START, END

from langchain_openai.chat_models import ChatOpenAI

# # Caso você deseja executar o Langfuse
# from langfuse.langchain import CallbackHandler
#
# # Initialize Langfuse CallbackHandler for Langchain (tracing)
# langfuse_handler = CallbackHandler()


def gera_temas_discussao(state: EntrevistaInput):
    class GeraTemasDiscussao(BaseModel):
      temas: list[str] = Field(description="Gere uma lista com 5 temas sobre o tópico citado.")

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    model_estruturado = model.with_structured_output(GeraTemasDiscussao)

    prompt_gerar_temas = f"""Você é o roterista de um podcast com anos de experiência.
Seu objetivo é a partir de um tópico, elaborar 5 temas que serão discutidos entre o entrevistador e o entrevistado sobre o tópico principal.

O Tópico é: `{state['topico']}`.

Agora elabore de forma estruturada os temas que serão abordados no programa."""
    resposta = model_estruturado.invoke([SystemMessage(content=prompt_gerar_temas)])
    return {'temas': resposta.temas}

def entrevistador(state: Entrevista):
    prompt_entrevistador_perguntas =f"""**Atue como um apresentador experiente de um podcast investigativo e altamente \
renomado.** Você tem mais de 15 anos de experiência entrevistando especialistas de diferentes áreas para uma audiência \
exigente que valoriza profundidade, originalidade e relevância prática.

Sua missão neste episódio é entrevistar um especialista altamente qualificado em **{state["topico"]}** com o objetivo de extrair \
**percepções que sejam ao mesmo tempo surpreendentes (não óbvias)** e **específicas (evitando generalidades, apoiadas \
por exemplos reais ou dados concretos)**.

### Temas que podem ser abordados sobre o tópico de discussão.
{state["temas"]}

### Como deve ser a exploração dos temas:

1. Todas as suas perguntas precisam revelar insights profundos, inesperados e fundamentados sobre o tema.
2. Ao longo da entrevista:
    - Explore exemplos práticos, estudos de caso, metáforas visuais ou histórias reais para tornar o conteúdo memorável.
    - Aprofunde em subtemas à medida que o especialista trouxer novos ângulos ou ideias.
    - Garanta que cada pergunta contribua para construir um entendimento cada vez mais refinado do assunto.
    - Manter um tom natural, engajado e inquisitivo durante toda a conversa, como se estivesse ao vivo.

### Orientação:
1. Analise o histórico da entrevista, quando existir para não fazer perguntas repetidas.
2. Se a entrevista não tiver sido iniciada, comece a entrevista com uma pergunta aberta e estratégica que convide \
o especialista a explorar o cerne do assunto.
3. Baseie suas próximas perguntas nas respostas anteriores, sempre tentando aprofundar ou desafiar gentilmente pontos apresentados.
4. Use expressões naturais de entrevistador como: "Você pode me dar um exemplo disso?", "Por que isso acontece assim?", \
"Existe alguma exceção a essa regra?", "Como isso se aplicaria no mundo real?", etc.
5. Quando considerar que os objetivos de profundidade, surpresa e especificidade foram plenamente atingidos, \
encerre a entrevista com: **"Muito obrigado pela sua ajuda."**

### Tarefa:
Com base nas orientações informadas, gere sempre APENAS UMA pergunta de cada vez seguindo rigorosamente as instruções.

### Nome do Entrevistado:
{state["entrevistado"]}

Mantenha-se no personagem do apresentador durante toda a resposta. Não quebre o papel. Seja curioso, crítico e \
elegante, conduzindo a conversa como um verdadeiro profissional.

**Importante:** evite respostas vagas ou genéricas. Cada resposta do especialista deve trazer algo memorável e \
digno de citação.

---

# Histórico:
"""

    model_entrevistador = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    pergunta = model_entrevistador.invoke([SystemMessage(content=prompt_entrevistador_perguntas)]+state["mensagens"])

    return {"mensagens": [pergunta]}

def rota_finalizou_ou_segue_pesquisa(state: Entrevista):
    last_question = state["mensagens"][-1]
    if "Muito obrigado pela sua ajuda" in last_question.content:
        return 'salva_entrevista'
    return "pesquisa_wikipedia"

def pesquisa_wikipedia(state: Entrevista):
    prompt_pesquisa =f"""**Atue como um engenheiro de busca experiente, especializado em transformar perguntas humanas \
em consultas otimizadas para sistemas de recuperação de informação e mecanismos de busca na web.** Você tem mais de 10 \
anos de experiência em engenharia de prompts, NLP e reformulação de perguntas para extração de informações relevantes.

Você receberá a transcrição completa de uma conversa entre o apresentador de um podcast popular e um especialista. \
Essa conversa culmina em uma pergunta final feita pelo apresentador (ou analista), que reflete o objetivo principal \
da entrevista.

### Seu objetivo:

Criar **uma consulta de busca bem estruturada, clara e altamente eficiente**, baseada nessa última pergunta, para uso \
em mecanismos de busca ou sistemas de recuperação de informação.

### Etapas que você deve seguir:

1. Leia e analise cuidadosamente **toda a conversa** entre o apresentador e o especialista.
2. Identifique a **última pergunta feita pelo apresentador** — essa pergunta costuma ser a mais estratégica e \
representa o foco final da investigação.
3. Reescreva essa pergunta como uma **consulta de busca otimizada**, com palavras-chave relevantes, estrutura \
sintética, e sem elementos supérfluos (ex: pronomes, subjetividades, redundâncias).
4. Certifique-se de que a consulta:

   * Seja adequada para motores de busca como Google, Bing ou ferramentas de recuperação semântica.
   * Mantenha o sentido e a intenção original da pergunta.
   * Use operadores ou reformulações quando necessário (ex: "como", "impacto de", "benefícios de", "tendências em", etc).

### Exemplo de entrada:

(Trecho de conversa completo entre apresentador e especialista)

### Exemplo de saída:

(Consulta estruturada como: `impacto da inteligência artificial na educação superior em países em desenvolvimento`)

Importante: **A saída deve ser apenas a consulta estruturada.** Não inclua explicações, introduções ou formatações adicionais."""

    class Pesquisa(BaseModel):
        consulta_pesquisa: str = Field(None, description="Consulta de pesquisa para recuperação de informação no wikipedia.")

    model_entrevistador = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    model_entrevistador_estruturado = model_entrevistador.with_structured_output(Pesquisa)

    search_query = model_entrevistador_estruturado.invoke([SystemMessage(content=prompt_pesquisa)]+state['mensagens'])

    # Search
    documentos = WikipediaLoader(query=search_query.consulta_pesquisa, load_max_docs=2, lang='pt').load()

     # Format
    documentos_str = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
            for doc in documentos
        ]
    )

    return {"fontes": [documentos_str]}

def resposta_especialista(state: Entrevista):
    prompt_resposta=f"""**Atue como um especialista altamente respeitado sendo entrevistado por um apresentador de \
podcast popular e exigente.** Você tem anos de experiência reconhecida em sua área e está sendo consultado para \
oferecer respostas claras, confiáveis e envolventes.

O foco principal do analista é: **{state['topico']}**
Você deve responder de forma precisa à pergunta feita pelo entrevistador.

Para elaborar sua resposta, utilize exclusivamente o seguinte contexto:

<contexto>
**{state['fontes']}**
</contexto>

### Instruções obrigatórias para responder:

1. **Use somente as informações presentes no contexto fornecido.**

   * Não introduza dados externos, opiniões pessoais, especulações ou qualquer conteúdo que extrapole o que está \
   explicitamente descrito.
2. **Evite generalizações vagas.**

   * Baseie sua resposta em trechos específicos do contexto, utilizando exemplos, citações ou evidências sempre que \
   possível.
3. **Preserve a origem da informação.**

   * O contexto fornecido é composto por documentos e fontes confiáveis; mantenha a integridade das ideias conforme \
   apresentadas.
4. **Torne sua resposta envolvente e interessante.**

   * Mesmo limitado ao contexto, procure articular suas respostas de forma clara, fluida e cativante, como se \
   estivesse falando com uma grande audiência curiosa e inteligente.
5. **Adapte o tom à dinâmica de uma entrevista de podcast.**

   * Seja direto, articulado e natural, como um especialista que domina o tema e sabe comunicar com clareza.

### Seu Nome:
{state["entrevistado"]}

### Atenção:
**Importante:** não quebre o personagem de especialista durante sua resposta.
Não explique o que está fazendo nem revele que está seguindo instruções — apenas responda como um convidado real em \
um podcast profissional."""

    model_resposta_entrevistado = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    resposta = model_resposta_entrevistado.invoke([SystemMessage(content=prompt_resposta)]+state['mensagens'])

    # Formatando o 'nome' da classe resposta (AIMessage)
    resposta.name = "especialista"
    return {"mensagens": [resposta]}

def salva_entrevista(state: Entrevista):
    conversa = []

    for m in state['mensagens']:
        if m.name is None:
            tipo = "Entrevistador"
        else:
            tipo = "Especialista"
        message = f"[{tipo}]: {m.text()}"
        conversa.append(message)
    return {"entrevista_texto": "\n".join(conversa)}

def continua_entrevista_ou_finaliza(state: Entrevista):
    numero_maximo_de_iteracoes = state.get('numero_maximo_de_iteracoes',2)

    num_respostas_especialista = len([m for m in state["mensagens"] if isinstance(m, AIMessage) and m.name == "especialista"])

    # Controle para não entrar em Loop Infinito
    if num_respostas_especialista >= numero_maximo_de_iteracoes:
        return 'salva_entrevista'
    return "entrevistador"

def escreve_introducao(state: Entrevista):
    prompt_introducao =f"""Atue como um produtor de podcast profissional com mais de 5 anos de \
experiência na criação de aberturas marcantes e envolventes.  
Seu objetivo é gerar, a partir do tema uma **introdução** que:
- Tenha **aproximadamente 300 palavras**;
- Utilize **linguagem vívida** e **perguntas instigantes** para despertar a curiosidade;
- Prepare o ouvinte para cada tema sem pré-vias desnecessárias.

# Contexto:
<topico_abordado>
{state["topico"]}
</topico_abordado>

<entrevista_realizada_com_expert>
{state["entrevista_texto"]}
</entrevista_realizada_com_expert>

### Nome do Entrevistado:
{state["entrevistado"]}

## Formato de saída:
Um texto de aproximadamente 300 palavras

# Fluxo de trabalho passo a passo

1. **Analise** o 'topico abordado' e os pontos da 'entrevista'.
2. **Estruture** a introdução:
   1. Comece com uma frase de impacto ou pergunta provocativa.
   2. Explore em poucas frases as principais ideias trazidas por cada segmento.
   3. Use transições suaves para conectar tópicos e manter o ouvinte engajado.
3. **Aplique** linguagem sensorial e exemplos rápidos para tornar o texto mais visual.
4. **Revise** para garantir clareza, concisão e coesão.

Entregue um conteúdo que fisgue a atenção desde a primeira palavra."""

    model_introducao = ChatOpenAI(model="gpt-4o", temperature=0.2)
    introducao = model_introducao.invoke([SystemMessage(content=prompt_introducao)])

    return {"introducao": introducao.content, "roteiro_final": [introducao]}

def revisao_fala_inicial(state: Entrevista):
    # Preciso ajustar as mensagens da entrevista (primeira pergunta e ultima dara criar continuidade no texto
    primeira_mensagem = state["mensagens"][0]  # Sempre é o entrevistador

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    prompt_ajuste_primeira_pergunta = f"""**Atue como um revisor experiente de um roteiro de podcast altamente \
renomado.** Você tem mais de 15 anos de experiência revisando roteiros complexos de diferentes áreas para uma audiência \
exigente que valoriza profundidade, originalidade e relevância prática.

Sua missão é observar a INTRODUÇÃO presente entre as tags <introducao> e corrigir o texto da primeira mensagem do entrevistador \
(apresentador do podcast) presente entre as tags <primeira_fala> com o seguinte objetivo: dar continuidade ao texto \
sem que possa parecer que houve uma quebra de contexto.

<introducao>
{state["introducao"]}
</introducao>

<primeira_fala>
{primeira_mensagem.content}
</primeira_fala>

# Instruções
- Evite explicações — apenas entregue o texto corrigido.
- NAO USE TAGS HTML!
- Não mude o assunto da fala, mantenha coesão no que foi comentado nesta primeira fala, apenas adapte para que seja \
uma fala que dê sequencia ao texto introdução para evitar quebras abruptas no contexto.
- Não invente assuntos novos."""

    primeira_fala_corrigida = model.invoke([SystemMessage(content=prompt_ajuste_primeira_pergunta)])

    return {"roteiro_final": [primeira_fala_corrigida]}

def escreve_conclusao(state: Entrevista):
    promtp_conclusao = f"""Atue como um produtor de podcast profissional com mais de 5 anos de experiência na criação \
de encerramentos memoráveis e impactantes.  
Seu objetivo é gerar, a partir do tema e dos principais segmentos do episódio, **uma conclusão envolvente** que:
- Tenha **aproximadamente 200 palavras**;
- Destaque os **insights mais relevantes** de cada bloco abordado;
- Termine com uma **declaração instigante** que incentive reflexão ou ação imediata;
- Evite encerramentos excessivos ou desnecessários.

### Nome do Entrevistado:
{state["entrevistado"]}

# Contexto:
<topico_abordado>
{state["topico"]}
</topico_abordado>

<introducao>
{state["introducao"]}
</introducao>

<entrevista_realizada_com_expert>
{state["entrevista_texto"]}
</entrevista_realizada_com_expert>

## Formato de saída:
Seu texto de aproximadamente 200 palavras.

**Fluxo de trabalho passo a passo**:

1. **Analise** o tópico, a introducao e a entrevista.
2. **Extraia** os três a cinco aprendizados ou insights mais fortes de cada segmento.
3. **Estruture** a conclusão:
   1. Recapitule brevemente o propósito do episódio.
   2. Sintetize os insights principais em frases claras e impactantes.
   3. Conecte esses insights de forma fluida.
4. **Crie** uma declaração final provocativa, que convide o ouvinte à reflexão ou ação prática.
5. **Revise** o texto para garantir concisão, coesão e tom inspirador.

Entregue um fechamento que deixe uma marca duradoura na mente do ouvinte."""

    model_conclusao = ChatOpenAI(model="gpt-4o", temperature=0.2)
    conclusao = model_conclusao.invoke([SystemMessage(content=promtp_conclusao)])
    return {"conclusao": conclusao.content}

def revisao_fala_pre_conclusao(state: Entrevista):
    # Preciso ajustar as mensagens da entrevista (primeira pergunta e ultima dara criar continuidade no texto
    ultima_mensagem = state["mensagens"][-1] # Pode ser o entrevistador ou o especialista
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    if "Muito obrigado pela sua ajuda" in ultima_mensagem:
        prompt_ajuste_ultima_pergunta = f"""****Atue como um revisor experiente de roteiros para podcasts de alto \
nível.** Você tem mais de 15 anos de experiência revisando, ajustando e refinando roteiros de entrevistas \
para programas consagrados, com foco em linguagem envolvente, fluidez narrativa e adaptação ao público exigente. \
Seu trabalho é garantir que cada fala soe natural, mantenha o ritmo da introdução e evite qualquer ruptura de contexto.

Sua missão é observar a CONCLUSÃO presente entre as tags <conclusao> e corrigir o texto da ultima mensagem do entrevistador \
(apresentador do podcast) presente entre as tags <ultima_fala> com o seguinte objetivo: corrigir esta ultima fala para\
que dê continuidade no texto sem quebras abruptas de contexto. Ou seja, esta ultima fala deve fluir de forma a \
combinar com a conclusão já escrita.

<conclusao>
{state["conclusao"]}
</conclusao>

<ultima_fala>
{ultima_mensagem.content}
</ultima_fala>

# Instruções
- Evite explicações — apenas entregue o texto corrigido.
- Não mude o assunto da fala, mantenha coesão no que foi comentado nesta ultima fala, apenas adapte para que seja \
uma mensagem que dê sequencia fluida para a conclusão.
- Não invente assuntos novos."""

        ultima_fala_corrigida = model.invoke([SystemMessage(content=prompt_ajuste_ultima_pergunta)])

        roteiro_final = state["mensagens"][1:-1] + [ultima_fala_corrigida] + [AIMessage(content=state["conclusao"])]

    else:
        prompt_ultima_fala_a_ser_inserida = f"""****Atue como um revisor experiente de roteiros para podcasts de alto \
nível.** Você tem mais de 15 anos de experiência revisando, ajustando e refinando roteiros de entrevistas \
para programas consagrados, com foco em linguagem envolvente, fluidez narrativa e adaptação ao público exigente. \
Seu trabalho é garantir que cada fala soe natural, mantenha o ritmo da introdução e evite qualquer ruptura de contexto.

Sua missão é observar a CONCLUSÃO e a ultima resposta do entrevistado presente entre as tags <ultima_fala_especialista> \
a fim de criar uma FALA DE AGRADECIMENTO que ANTECEDE à CONCLUSÃO.

<conclusao>
{state["conclusao"]}
</conclusao>

<ultima_fala_especialista>
{ultima_mensagem.content}
</ultima_fala_especialista>

# Instruções
- NÃO USE TAGS HTML
- Evite explicações — apenas entregue o texto corrigido.
- NÃO REPITA A CONCLUSÃO. ESCREVA APENAS A FALA DE AGRADECIMENTO QUE ANTECEDE À CONCLUSÃO AGRADECENDO O ENTREVISTADO, \
por exemplo: `Muito obrigado pela sua entrevista...`"""

        ultima_fala_inserida = model.invoke([SystemMessage(content=prompt_ultima_fala_a_ser_inserida)])

        roteiro_final = state["mensagens"][1:] + [ultima_fala_inserida] + [AIMessage(content=state["conclusao"])]

    return {"roteiro_final": roteiro_final}


# Graph
graph = StateGraph(Entrevista, input_schema=EntrevistaInput, output_schema=EntrevistaOutput)

graph.add_node("gera_temas_discussao", gera_temas_discussao)
graph.add_node("entrevistador", entrevistador)
graph.add_node("pesquisa_wikipedia", pesquisa_wikipedia)
graph.add_node("resposta_especialista", resposta_especialista)
graph.add_node("salva_entrevista", salva_entrevista)
graph.add_node("escreve_introducao", escreve_introducao)
graph.add_node("revisao_fala_inicial", revisao_fala_inicial)
graph.add_node("escreve_conclusao", escreve_conclusao)
graph.add_node("revisao_fala_pre_conclusao", revisao_fala_pre_conclusao)



# Flow
graph.add_edge(START, "gera_temas_discussao")
graph.add_edge("gera_temas_discussao", "entrevistador")
graph.add_conditional_edges("entrevistador", rota_finalizou_ou_segue_pesquisa,
                            {'pesquisa_wikipedia':'pesquisa_wikipedia', 'salva_entrevista':'salva_entrevista'})
graph.add_edge("pesquisa_wikipedia", "resposta_especialista")
graph.add_conditional_edges("resposta_especialista", continua_entrevista_ou_finaliza,
                            {'salva_entrevista':'salva_entrevista', 'entrevistador':'entrevistador'})
graph.add_edge("salva_entrevista", "escreve_introducao")
graph.add_edge("escreve_introducao", "revisao_fala_inicial")
graph.add_edge("revisao_fala_inicial", "escreve_conclusao")
graph.add_edge("escreve_conclusao", "revisao_fala_pre_conclusao")
graph.add_edge("revisao_fala_pre_conclusao", END)


# Grafo Compilado
app = graph.compile()

# ---------------------------------------------------------------------------------------------------------------------

# # Imprimindo a Imagem do Grafo:
# import io
# from PIL import Image
# img_bytes = app.get_graph(xray=1).draw_mermaid_png()
# img = Image.open(io.BytesIO(img_bytes))
# img.save('diagrama_workflow_game.png')
# img.show()

# ---------------------------------------------------------------------------------------------------------------------

# # Fazer streaming de eventos do State:
# for s in app.stream(
#     {"topico": "Politica Brasileira"},
#     config={"callbacks": [langfuse_handler]}):
#     print(s)

# ---------------------------------------------------------------------------------------------------------------------
# # Invocando o Grafo completo S/ langfuse:
# resposta_app = app.invoke({"topico": "Viagens pelo mundo. Conhecendo lugares inimagináveis.",
#                 "entrevistado": "Influencer: Sara, do canal Viagens da Sara."})
#
# print(resposta_app)
# ---------------------------------------------------------------------------------------------------------------------


# # Invocando o Grafo completo c/ langfuse:
# resposta_app = app.invoke({"topico": "Viagens pelo mundo. Conhecendo lugares inimagináveis.",
#                 "entrevistado": "Influencer: Sara, do canal Viagens da Sara."},
#                config={"callbacks": [langfuse_handler]})


