# 🛰️ Sentinela Estuarino — Agente Autônomo para Monitoramento do Rio Poxim

Sistema de agente inteligente para monitoramento ambiental do estuário do Rio Poxim (Aracaju-SE), implementado com base no framework **AIMA** (Russell & Norvig). O drone autônomo navega em um grid 10×10 representando a região do estuário, utilizando **busca A*** para planejar rotas ótimas de coleta de amostras de poluição.

---

## 🧠 Modelagem do Problema

### Descrição PEAS

| Componente | Descrição |
|------------|-----------|
| **Performance** | Coletar todas as amostras de poluição, minimizar consumo de bateria, retornar à base |
| **Ambiente** | Grid 10×10 do estuário do Rio Poxim com zonas urbanas, mangues e pontos de coleta |
| **Atuadores** | Movimentação (N/S/L/O), coleta de amostras |
| **Sensores** | GPS (posição), bateria, detecção de amostras próximas, tipo de zona |

### Classificação do Ambiente

| Propriedade | Classificação | Justificativa |
|-------------|---------------|---------------|
| Observabilidade | Parcialmente observável | O drone percebe apenas o entorno imediato |
| Agentes | Mono-agente | Um único drone sentinela |
| Determinismo | Determinístico | As ações têm efeitos previsíveis no grid |
| Episodicidade | Sequencial | Cada ação afeta os estados futuros |
| Dinamismo | Estático | O ambiente não muda durante o planejamento |
| Continuidade | Discreto | Grid de células inteiras |

### Estado, Ações e Objetivo

**Estado:** `(pos_x, pos_y, bateria, frozenset(alvos_pendentes))`

**Ações:** `CIMA`, `BAIXO`, `ESQUERDA`, `DIREITA`, `COLETAR`

**Objetivo:** `alvos_pendentes == ∅` ∧ `posição == base(0,0)` ∧ `bateria > 0`

**Custo das ações:**
- Movimento em área natural: **−1 bateria**
- Movimento em zona urbana (Urban Penalty): **−3 bateria**
- Passagem por obstáculo de mangue: **bloqueada**

---

## � Algoritmos de Busca e Heurísticas

### Algoritmo Principal: A*

O agente utiliza `astar_search` do repositório AIMA com função de avaliação:

```
f(n) = g(n) + h(n)
```

onde:
- `g(n)` = custo acumulado do caminho (com Urban Penalty)
- `h(n)` = heurística admissível de Manhattan ajustada

### Heurística: Manhattan + Vento Atlântico

```python
h(n) = |Δx| * fator_vento + |Δy| + custo_retorno_base
```

O **fator de Vento Atlântico** (1.5×) penaliza movimentos para leste, refletindo as condições reais de vento predominante em Aracaju. A heurística é **admissível** porque nunca superestima: o fator 1.5× é menor ou igual ao custo real de deslocamento contra o vento, e a estimativa de retorno à base usa sempre a distância Manhattan mínima.

### Arquitetura Ambiente–Agente–Programa

```
┌─────────────────────────────────────────────┐
│              PoximEnvironment               │  ← XYEnvironment (AIMA)
│  - Grid 10×10 com obstáculos e zonas        │
│  - execute_action() com Urban Penalty       │
│  - percept() retorna estado local           │
└────────────────┬────────────────────────────┘
                 │ percept / action
┌────────────────▼────────────────────────────┐
│          AutonomousDroneAgent               │  ← SimpleProblemSolvingAgentProgram (AIMA)
│  1. update_state(percept)                   │
│  2. formulate_goal(state)                   │
│  3. formulate_problem(state, goal)          │
│  4. search(problem) → astar_search()        │
└────────────────┬────────────────────────────┘
                 │ PollutionMappingProblem
┌────────────────▼────────────────────────────┐
│         PollutionMappingProblem             │  ← Problem (AIMA)
│  - actions(), result(), goal_test()         │
│  - path_cost() com Urban Penalty            │
│  - h() com ajuste de Vento Atlântico        │
└─────────────────────────────────────────────┘
```

---

## 📦 Estrutura de Arquivos

```
inteligencia-artificial-ufs/
├── aima-python/                  # Biblioteca AIMA (clone externo)
├── env/estuario.py               # PoximEnvironment — mundo do agente
├── problems/search_problem.py    # PollutionMappingProblem — busca A*
├── drone_agents/
│   ├── drone_agent.py            # AutonomousDroneAgent — programa do agente
│   └── api_gateway.py            # Comunicação com API de chamados
├── interfaces/sensor_interfaces.py  # Abstrações de sensores
├── app.py                        # API de gerenciamento de chamados
├── main.py                       # Implementação inicial (preservada)
├── main_autonomous.py            # Loop de simulação completo
└── requirements.txt
```

---

## 🚀 Como Executar

### Pré-requisitos

1. Python 3.11+
2. Clonar a biblioteca AIMA:
   ```bash
   git clone https://github.com/aimacode/aima-python.git
   ```
3. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   pip install numpy ipythonblocks
   ```

### Simulação Autônoma (modo offline)

```bash
python main_autonomous.py --simulacao
```

### Com API de Chamados (modo completo)

```bash
# Terminal 1 — inicia o servidor de missões
python app.py

# Terminal 2 — executa o agente
python main_autonomous.py
```

### Implementação original (`main.py`)

```bash
python main.py
```

---

## 📊 Exemplo de Saída

```
  🛰️  SISTEMA ADEMA-DRONE — Monitoramento do Rio Poxim
================================================================
📋 Chamados abertos: 3
   #1: Amostragem Ponto Norte - Mangue Degradado @ (7, 2)
   #2: Verificação de Metais Pesados @ (3, 8)
   #3: Monitoramento Biodiversidade - Caranguejos @ (8, 6)

🎯 Objetivo: (7, 2) | Bateria: 60
  � Executando A* Search...
  ✈️  Plano: ['DIREITA'×7, 'BAIXO'×2, 'COLETAR'] (10 ações)

  📊 RELATÓRIO FINAL
  Passos executados:   35
  Chamados coletados:  3/3
  Bateria restante:    25/60
  Na base:             ✅ Sim
  Missão completa:     ✅ Sim
```

**Legenda do grid:** 🤖 Drone | 🔴 Amostra | 🌿 Mangue | 🏙️ Zona Urbana

---
