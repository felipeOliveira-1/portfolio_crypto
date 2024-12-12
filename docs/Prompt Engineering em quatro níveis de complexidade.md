Abaixo apresentamos um guia didático, baseado no conteúdo da transcrição fornecida, que explica o conceito de Prompt Engineering em quatro níveis de complexidade. O objetivo é ensinar de forma clara e estruturada como criar prompts cada vez mais poderosos, tornando-os reutilizáveis, escalonáveis e integrados em aplicações reais. Ao final, você entenderá a importância do “prompt” como a unidade fundamental do trabalho com modelos de linguagem (LLMs).

---

## Introdução

Com a evolução dos modelos de linguagem (LLMs) e ferramentas locais como *Quinn 2.5*, o ato de "promptar" – isto é, de fornecer instruções textuais que o modelo deve seguir – tornou-se uma habilidade valiosa. A engenharia de prompts (Prompt Engineering) já não é algo trivial ou “uma piada”; hoje é uma competência fundamental para obter o máximo de ferramentas de IA em 2025 e além.

Uma das chaves para evoluir suas habilidades é entender que existem diferentes níveis de prompts. Eles variam desde o uso simples e pontual (Nível 1) até prompts completos e estruturados, capazes de serem integrados em aplicações complexas (Nível 4).

---

## O Conceito de Níveis de Prompt

**Nível 1: Prompt Simples (Ad Hoc)**  
- Prompts diretos, escritos “na hora” para obter uma resposta rápida.  
- Focados em uma única tarefa, sem formatação estruturada.  
- Fácil de testar com diferentes modelos, mas menos reutilizável.

**Nível 2: Prompt Estruturado e Reutilizável**  
- Introdução de estrutura (como tags XML ou HTML simples) para dar contexto e organização.  
- Inclui variáveis “estáticas” (por exemplo, um bloco de código ou instruções fixas) que você pode alterar com o tempo.  
- Melhor desempenho e consistência quando comparado aos prompts do Nível 1.

**Nível 3: Prompt Estruturado com Exemplos (Exemplos Guiam a Saída)**  
- Além da estrutura, são fornecidos exemplos concretos do formato de saída desejado.  
- Os exemplos ajudam a LLM a entender exatamente o tipo de resposta esperada.  
- Torna o prompt ainda mais robusto e consistente.

**Nível 4: Prompt Completo, Templetizado e Programável**  
- O prompt é transformado em um template com variáveis dinâmicas.  
- Pode ser integrado diretamente em aplicações via código, escalando infinitamente.  
- Inclui propósito, instruções, exemplos e placeholders para variáveis dinâmicas que são preenchidas pelo sistema (como texto do usuário, transcrições, dados externos etc.).

---

## Práticas Recomendadas no Desenvolvimento de Prompts

1. **Usar Estrutura de Marcação (como XML/HTML)**:  
   A web é repleta de HTML/XML, e os modelos foram treinados com tais estruturas. Formatação coerente e limpa melhora a compreensão do modelo.

2. **Instruções Claras e Curtas**:  
   Liste instruções objetivas, como “Use dialecto do Postgres” ou “Forneça apenas o código SQL”.

3. **Exemplos Consistentes**:  
   Inclua exemplos de entrada e saída. Isso dá ao modelo um “mapa mental” do que você espera.

4. **Variáveis Estáticas e Dinâmicas**:  
   - **Estáticas**: partes do prompt que não mudam (ex: instruções).  
   - **Dinâmicas**: partes que mudam a cada execução (ex: texto a ser sumarizado, nome de uma tabela, conteúdo de um arquivo).

5. **Testar em Diferentes Modelos**:  
   Use ferramentas de linha de comando (CLI) como `llm` ou `olama` para rapidamente testar seu prompt com diversos modelos, locais ou na nuvem.

6. **Construir uma Biblioteca de Prompts**:  
   Ter uma coleção organizada de prompts (por exemplo, em arquivos .xml) permite rápido acesso, reutilização e melhoria contínua.

---

## Exemplos Práticos

### Exemplo de Prompt Nível 1 (Ad Hoc)

Um prompt simples, executado diretamente na CLI:

```bash
# Arquivo: prompt.txt
Conte até 10 e depois volte a contar até 0.

# Executando via CLI (usando llm):
llm < prompt.txt
```

*Possível saída do modelo:*  
```
0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
9, 8, 7, 6, 5, 4, 3, 2, 1, 0
```

A mudança de uma palavra no prompt muda completamente a resposta. Sem estrutura, é um prompt útil apenas para a tarefa imediata.

---

### Exemplo de Prompt Nível 2 (Estruturado com Instruções Claras)

Aqui criamos um prompt para converter um tipo de dado (por exemplo, um interface TypeScript) em uma tabela SQL Postgres, usando XML para organizar:

```xml
<!-- Arquivo: ts_to_sql_table.xml -->
<prompt>
  <purpose>
    Converter a interface TypeScript em um CREATE TABLE no Postgres.
  </purpose>

  <instructions>
    <instruction>Use o dialeto Postgres</instruction>
    <instruction>Responda apenas com a definição da tabela</instruction>
  </instructions>

  <interface_block>
    interface User {
      id: string;
      email: string;
      created: string;
      isMember: boolean;
    }
  </interface_block>
</prompt>
```

Executando:

```bash
llm -m gpt-4 < ts_to_sql_table.xml
```

*Possível saída:*

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  created TIMESTAMP NOT NULL,
  is_member BOOLEAN NOT NULL
);
```

Note que agora o prompt é facilmente reutilizável: basta trocar o bloco de interface para gerar novas tabelas.

---

### Exemplo de Prompt Nível 3 (Com Exemplos)

Agora adicionamos um exemplo de saída para orientar o modelo a formatar a resposta de forma específica. Suponha que queremos resumir um texto em markdown com seções bem definidas.

```xml
<!-- Arquivo: spicy_summarize.xml -->
<prompt>
  <purpose>
    Summarizar um texto dado em um formato Markdown específico.
  </purpose>

  <instructions>
    <instruction>Saída em Markdown</instruction>
    <instruction>Sumarizar em 4 seções: Título, Resumo de Alto Nível, Pontos Principais, Sentimento</instruction>
    <instruction>Depois adicionar "Hot takes" a favor e contra o autor</instruction>
    <instruction>Use o mesmo formato do "example_output"</instruction>
  </instructions>

  <example_output>
    # Título
    - Resumo Alto Nível: ...
    - Pontos Principais: ...
    - Sentimento: ...
    - Hot Takes (Pró): ...
    - Hot Takes (Contra): ...
  </example_output>

  <content>
    Aqui inseriríamos o texto a ser resumido (dinâmico), por exemplo:
    "Este é um texto sobre a adoção de modelos de linguagem locais..."
  </content>
</prompt>
```

Executando:

```bash
llm -m gpt-4 < spicy_summarize.xml > resumo.md
```

*Possível saída:*

```markdown
# Título
- Resumo Alto Nível: O texto explora a adoção de modelos de linguagem locais e sua crescente importância.
- Pontos Principais: 
  - Modelos locais estão mais acessíveis.
  - Ferramentas CLI facilitam testes rápidos.
  - ...
- Sentimento: Otimista em relação à evolução dos LLMs.

- Hot Takes (Pró): 
  - Potencial de independência de grandes provedores.
  - Maior privacidade.
  - Menos dependência de APIs externas.

- Hot Takes (Contra):
  - Necessidade de hardware poderoso.
  - Complexidade de manutenção.
  - Curva de aprendizado técnica.
```

---

### Exemplo de Prompt Nível 4 (Templates Dinâmicos em Aplicação)

Um prompt nível 4 é integrado a uma aplicação, substituindo variáveis dinamicamente. Por exemplo, gerar capítulos de vídeo para YouTube com base em uma transcrição:

```xml
<!-- Arquivo: youtube_chapters.xml -->
<prompt>
  <purpose>
    Gerar capítulos para um vídeo do YouTube.
  </purpose>

  <instructions>
    <instruction>Use marcadores de tempo do transcript</instruction>
    <instruction>Crie títulos curtos e descritivos</instruction>
    <instruction>Adicione SEO keyword no título do capítulo</instruction>
  </instructions>

  <examples>
    <example>
      <input_transcript>... (exemplo de transcript) ...</input_transcript>
      <output>
        00:00 - Introdução (SEO Keyword)
        01:30 - Contexto Histórico (SEO Keyword)
        ...
      </output>
    </example>
  </examples>

  <variables>
    <seo_keyword>{{SEO_KEYWORD}}</seo_keyword>
    <transcript>{{VIDEO_TRANSCRIPT}}</transcript>
  </variables>
</prompt>
```

No código da aplicação, você pode substituir `{{SEO_KEYWORD}}` e `{{VIDEO_TRANSCRIPT}}` dinamicamente:

```python
# Exemplo Python
prompt_template = open("youtube_chapters.xml").read()
final_prompt = prompt_template.replace("{{SEO_KEYWORD}}", "IA Avançada") \
                              .replace("{{VIDEO_TRANSCRIPT}}", transcript_text)

# Em seguida, enviar `final_prompt` para um LLM via API e receber a resposta formatada.
```

---

## Conclusão

A jornada pelos quatro níveis de prompts mostra a evolução de simples instruções até templates complexos, escaláveis e integrados em sistemas. Ao dominar a engenharia de prompts, você ganha o poder de aproveitar ao máximo o mundo da IA generativa.

- **Nível 1:** Rápido, sem estrutura, útil para testes pontuais.  
- **Nível 2:** Estrutura e reusabilidade.  
- **Nível 3:** Exemplos guiam a formatação e a consistência.  
- **Nível 4:** Integração total em aplicações, escalabilidade e automação.

Aproveite essas práticas, construa sua própria biblioteca de prompts e esteja pronto para as inovações que 2025 trará.