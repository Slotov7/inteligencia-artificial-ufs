# 🛰️ Sentinela Estuarino — Agente Inteligente para Monitoramento do Rio Poxim

Sistema de agente autônomo (drone sentinela) para monitoramento ambiental do estuário do Rio Poxim, em Aracaju-SE. Utiliza algoritmos de busca (A*) do framework AIMA para navegação inteligente, integrado com uma API Flask de gestão de chamados/missões.

O projeto segue os **princípios SOLID** e a arquitetura de agentes de Russell & Norvig (AIMA), garantindo código modular, escalável e sem "God Classes".

---

## 📂 Estrutura do Projeto

```
inteligencia-artificial-ufs/
├── aima-python/                     # Biblioteca AIMA (clone externo)
├── interfaces/
│   └── sensor_interfaces.py         # Protocolos de sensores (ISP/DIP)
├── env/
│   └── estuario.py                  # Ambiente estuarino (SRP)
├── problems/
│   └── search_problem.py            # Problema de busca A* (OCP)
├── drone_agents/
│   ├── api_gateway.py               # Gateway de comunicação com API (SRP)
│   └── drone_agent.py               # Agente autônomo do drone (LSP)
├── app.py                           # API Flask — gestão de chamados
├── main.py                          # Implementação original (preservada)
├── main_autonomous.py               # Loop de coordenação do sistema
├── requirements.txt                 # Dependências do projeto
└── README.md                        # Este arquivo
```

---

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Git

## 🚀 Instalação e Configuração

1. **Clone este repositório** (se ainda não o fez):
   ```bash
   git clone https://github.com/Slotov7/inteligencia-artificial-ufs.git
   cd inteligencia-artificial-ufs
   ```

2. **Clone a biblioteca `aima-python`**:
   ```bash
   git clone https://github.com/aimacode/aima-python.git
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   pip install numpy ipythonblocks
   ```

---

## ▶️ Como Executar

### Simulação Autônoma (modo offline)

Executa o agente com dados simulados, sem precisar da API Flask:

```bash
python main_autonomous.py --simulacao
```

### Com API Flask (modo completo)

1. Inicie o servidor de chamados em um terminal:
   ```bash
   python app.py
   ```
2. Em outro terminal, execute o agente:
   ```bash
   python main_autonomous.py
   ```

### Implementação Original

O `main.py` original continua funcional:

```bash
python main.py
```

---

## 🧠 Arquitetura do Sistema

### Princípios SOLID Aplicados

| Princípio | Aplicação |
|-----------|-----------|
| **SRP** — Responsabilidade Única | `PoximEnvironment` gerencia o mundo; `APIGateway` gerencia comunicação; `AutonomousDroneAgent` gerencia decisões |
| **OCP** — Aberto/Fechado | `PollutionMappingProblem` aceita novos algoritmos de busca sem modificação |
| **LSP** — Substituição de Liskov | `AutonomousDroneAgent` pode ser substituído por `DroneManual` sem quebrar o ambiente |
| **ISP** — Segregação de Interface | Interfaces separadas para telemetria, sensores químicos, proximidade e visão |
| **DIP** — Inversão de Dependência | O agente depende de abstrações (`Protocol`), não de implementações concretas |

### Descrição PEAS do Agente

| Componente | Descrição |
|------------|-----------|
| **Performance** | Cobertura da área, detecção de poluentes, minimização de bateria, Urban Penalty |
| **Ambiente** | Estuário do Rio Poxim, grid 10×10, zonas urbanas, obstáculos de mangue |
| **Atuadores** | Movimentação (4 direções), coleta de amostras |
| **Sensores** | Posição GPS, bateria, detecção de amostras, zona urbana |

### Algoritmo A* com Vento Atlântico

O drone utiliza busca A* com heurística admissível baseada na **distância de Manhattan ajustada pelo Vento Atlântico**:

- Movimentos contra o vento predominante de leste recebem fator 1.5×
- Zonas urbanas aplicam **Urban Penalty** de 3× no custo de bateria
- A heurística é admissível e consistente, garantindo caminho ótimo

### API de Chamados

A API Flask (`app.py`) gerencia missões com autenticação HTTP Basic:

- **Credenciais**: `admin` / `123456`
- **Endpoints**: `GET/POST/PUT/DELETE /chamados`
- **Status**: `aberto` → `em_andamento` → `fechado`

---

## 📊 Exemplo de Saída

```
================================================================
  🛰️  SISTEMA ADEMA-DRONE — Monitoramento do Rio Poxim
================================================================

📋 Chamados abertos sincronizados: 3
   #1: Amostragem Ponto Norte - Mangue Degradado @ (7, 2)
   #2: Verificação de Metais Pesados - Zona Industrial @ (3, 8)
   #3: Monitoramento Biodiversidade - Caranguejos @ (8, 6)

========================================
  Grid do Estuário (10×10)
========================================
   0 | 🤖 ·  ·  ·  ·  ·  ·  ·  ·  ·
   1 | ·  🏙️ 🏙️ 🏙️ ·  ·  ·  ·  ·  ·
   2 | ·  🏙️ 🏙️ ·  ·  ·  ·  🔴 ·  ·
   3 | ·  ·  ·  ·  🏙️ 🏙️ 🌿 ·  ·  ·
   4 | ·  ·  ·  ·  🌿 🌿 ·  🌿 ·  ·
   5 | ·  ·  ·  ·  ·  🏙️ 🏙️ ·  ·  ·
   6 | ·  ·  🌿 ·  ·  ·  ·  ·  🔴 ·
   7 | ·  ·  ·  ·  ·  ·  ·  ·  ·  ·
   8 | ·  ·  ·  🔴 ·  ·  ·  ·  ·  ·
   9 | ·  ·  ·  ·  ·  ·  ·  ·  ·  ·

  📊 RELATÓRIO FINAL DA MISSÃO
  Passos executados:      35
  Chamados processados:   3/3
  Bateria restante:       25/60
  Missão completa:        ✅ Sim
```

**Legenda**: 🤖 Drone | 🔴 Amostra | 🌿 Mangue | 🏙️ Zona Urbana

---

## 👥 Autores

- Projeto desenvolvido para a disciplina de Inteligência Artificial — Universidade Federal de Sergipe (UFS)
