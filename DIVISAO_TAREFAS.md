# 📋 Divisão de Tarefas — Sentinela Estuarino do Rio Poxim

**Disciplina:** Inteligência Artificial — UFS  
**Projeto:** Agente Autônomo para Monitoramento Ambiental do Estuário do Rio Poxim  
**Repositório:** https://github.com/Slotov7/inteligencia-artificial-ufs

---

## ✅ O que já foi feito

### Samuel — Modelagem Inicial do Problema
- Criou a classe `SentinelaEstuarino(Problem)` no `main.py`
- Implementou o algoritmo A* com heurística de Manhattan
- Definiu o estado `(x, y, bateria, alvos_pendentes)`
- Implementou `actions()`, `result()`, `goal_test()` e `h()`

### Miguel — Arquitetura SOLID e Integração Completa
- **`app.py`** — API Flask com autenticação HTTP Basic e CRUD de chamados/missões
- **`env/estuario.py`** — Classe `PoximEnvironment(XYEnvironment)` com Urban Penalty (3× bateria em zonas urbanas), coleta de amostras e visualização do grid
- **`problems/search_problem.py`** — Classe `PollutionMappingProblem(Problem)` com heurística de Manhattan + Vento Atlântico
- **`drone_agents/drone_agent.py`** — Classe `AutonomousDroneAgent(SimpleProblemSolvingAgentProgram)` com ciclo completo de busca
- **`drone_agents/api_gateway.py`** — Classe `APIGateway` isolando comunicação HTTP com a API (com fallback para simulação offline)
- **`interfaces/sensor_interfaces.py`** — Protocolos abstratos para sensores (ISP/DIP)
- **`main_autonomous.py`** — Script de coordenação que integra tudo
- **`README.md`** — Documentação completa do projeto

---

## 🔜 O que falta fazer

---

### 🧠 Guilherme — Inteligência Avançada e Análise de Algoritmos

**Objetivo:** Evoluir o "cérebro" do agente e provar que o A* é a melhor escolha.

#### Tarefa 1: Comparação de Algoritmos de Busca
- Criar o arquivo `analise_algoritmos.py`
- Implementar **BFS (Busca em Largura)** e **Greedy Best-First** como alternativas ao A*
- Rodar os 3 algoritmos com os mesmos chamados e gerar uma tabela comparativa com:
  - Número de nós expandidos
  - Tempo de execução (em ms)
  - Custo total do caminho
  - Bateria consumida
- **Referência AIMA:** Capítulos 3 e 4

#### Tarefa 2: Agente Baseado em Utilidade
- Melhorar o método `formulate_goal()` em `drone_agents/drone_agent.py`
- Implementar cálculo de **Utilidade Máxima Esperada (MEU)**: quando a bateria está abaixo de 30%, calcular `U(ir ao alvo) vs U(voltar à base)` considerando distância e risco
- **Referência AIMA:** Capítulo 16

#### Tarefa 3: Rede Bayesiana para Diagnóstico de Poluição
- Criar a pasta `bayesian/` com o arquivo `diagnostico_poluicao.py`
- Implementar uma rede bayesiana simples com nós:
  - `Maré` (Baixa/Alta)
  - `Proximidade Urbana` (Sim/Não)
  - `Saúde do Mangue` (Boa/Degradada)
  - → Inferir `P(poluição grave | evidências dos sensores)`
- Usar as leituras do `ChemicalSensor` de `interfaces/sensor_interfaces.py`
- **Referência AIMA:** Capítulos 12 e 13

**Arquivos que o Guilherme cria/modifica:**
```
analise_algoritmos.py          (NOVO)
bayesian/__init__.py           (NOVO)
bayesian/diagnostico_poluicao.py  (NOVO)
drone_agents/drone_agent.py    (MELHORIA no formulate_goal)
```

---

### 🧪 João Antônio — Testes, Validação e Benchmark

**Objetivo:** Provar que o sistema funciona corretamente e não quebra em nenhum cenário.

#### Tarefa 1: Suíte de Testes com `pytest`
- Criar a pasta `tests/` com os seguintes arquivos de teste:

| Arquivo de Teste | O que valida |
|------------------|--------------|
| `test_urban_penalty.py` | Zonas urbanas gastam exatamente 3× de bateria |
| `test_heuristica.py` | `h(n)` nunca superestima o custo real (admissibilidade) |
| `test_goal.py` | `goal_test` só retorna True com alvos vazios + na base + bateria ≥ 0 |
| `test_api_fallback.py` | `APIGateway` cai no modo simulação quando a API está offline |
| `test_obstaculos.py` | O drone nunca atravessa mangues/obstáculos |
| `test_actions.py` | `actions()` nunca retorna movimentos para fora do grid |

#### Tarefa 2: Benchmark de Desempenho
- Criar o arquivo `benchmark.py`
- Rodar a missão **100 vezes** com alvos em posições aleatórias
- Calcular e exibir:
  - Taxa de sucesso (%)
  - Média de bateria restante
  - Desvio padrão
  - Pior caso vs melhor caso

#### Tarefa 3: Script de Validação Rápida
- Criar um `Makefile` ou `run_tests.py` que execute tudo de uma vez:
  ```bash
  pytest tests/ -v
  python main_autonomous.py --simulacao
  python benchmark.py
  ```

**Arquivos que o João cria:**
```
tests/__init__.py              (NOVO)
tests/test_urban_penalty.py    (NOVO)
tests/test_heuristica.py       (NOVO)
tests/test_goal.py             (NOVO)
tests/test_api_fallback.py     (NOVO)
tests/test_obstaculos.py       (NOVO)
tests/test_actions.py          (NOVO)
benchmark.py                   (NOVO)
```

---

### 📝 Débora — Documentação Técnica, Vídeo e Apresentação

**Objetivo:** Transformar o projeto técnico em uma apresentação que garanta a nota máxima.

#### Tarefa 1: Relatório Técnico Final (PDF)
O relatório deve conter:
- **Contextualização socioambiental**: degradação do Rio Poxim, caranguejo-uçá (Ucides cordatus), guaiamum (Cardisoma guanhumi), impacto do esgoto nas comunidades extrativistas
- **Tabela PEAS completa** com referências ao Capítulo 2 do AIMA
- **Classificação do ambiente**: parcialmente observável, estocástico, sequencial, dinâmico, contínuo — com justificativa para cada item
- **Prova de admissibilidade da heurística** Manhattan + Vento Atlântico
- **Diagrama de arquitetura SOLID** mostrando as dependências entre os módulos
- **Resultados**: tabela comparativa de algoritmos (dados do Guilherme) e métricas de teste (dados do João)

#### Tarefa 2: Vídeo Demonstrativo (3-5 minutos)
- Rodar `python main_autonomous.py --simulacao` e gravar a tela
- Narrar os momentos de decisão do agente:
  - "Aqui o A* calculou a rota evitando mangues"
  - "Neste ponto, a Urban Penalty aumentou o custo de bateria em 3×"
  - "O drone decidiu retornar à base com 42% de bateria restante"
- Mostrar o grid visual antes e depois da missão

#### Tarefa 3: Slides de Apresentação
- Slide de título com o problema
- Contextualização do Rio Poxim
- Arquitetura do sistema (diagrama SOLID)
- Demonstração visual dos resultados
- Conclusão e próximos passos

**Arquivos que a Débora cria:**
```
docs/relatorio_final.pdf       (NOVO)
docs/slides_apresentacao.pptx  (NOVO)
docs/video_demonstracao.mp4    (NOVO)
```

---

## 📊 Quadro Resumo

| Membro | Papel | Arquivos | Referência AIMA |
|--------|-------|----------|-----------------|
| **Samuel** ✅ | Modelagem inicial | `main.py` | Cap. 3 |
| **Miguel** ✅ | Arquitetura SOLID + Integração | `env/`, `problems/`, `drone_agents/`, `interfaces/`, `app.py`, `main_autonomous.py` | Cap. 2-4 |
| **Guilherme** 🔜 | Inteligência avançada + Bayes | `analise_algoritmos.py`, `bayesian/`, melhoria no agente | Cap. 3, 4, 12, 13, 16 |
| **João** 🔜 | Testes + Validação + Benchmark | `tests/`, `benchmark.py` | Eng. de Software |
| **Débora** 🔜 | Relatório + Vídeo + Slides | `docs/` | Cap. 2, 3 (teoria) |

---

## ⚠️ Regras Importantes

1. **Cada pessoa faz commits nos SEUS arquivos** — não mexam nos arquivos dos outros sem combinar
2. **Sempre rodem `python main_autonomous.py --simulacao` antes de commitar** para garantir que nada quebrou
3. **Guilherme**: não modifique a assinatura dos métodos existentes — apenas adicione lógica nova
4. **João**: os testes devem rodar com `pytest tests/ -v` sem precisar da API Flask
5. **Débora**: peça os dados dos resultados para o Guilherme e o João antes de montar o relatório
