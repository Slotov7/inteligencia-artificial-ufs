# Sentinela Estuarino - Agente Inteligente

Este projeto implementa um agente inteligente (drone sentinela) utilizando algoritmos de busca para navegar em um ambiente estuarino, coletar amostras e retornar à base, evitando obstáculos. O projeto utiliza a biblioteca `aima-python` como base para os algoritmos de Inteligência Artificial.

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Git

## 🚀 Instalação e Configuração

Siga os passos abaixo para configurar o ambiente:

1. **Clone este repositório** (se ainda não o fez):

   ```bash
   git clone <https://github.com/Slotov7/inteligencia-artificial-ufs.git>
   cd inteligencia-artificial-ufs
   ```

2. **Clone a biblioteca `aima-python`**:
   O projeto depende da biblioteca `aima-python` localizada dentro do diretório raiz. Execute:
   ```bash
   git clone https://github.com/aimacode/aima-python.git
   ```
   _Nota: O script `main.py` já está configurado para adicionar esta pasta ao caminho do Python._

## ▶️ Como Executar

Para iniciar a simulação do agente, execute o arquivo principal:

```bash
python main.py
```

## 📂 Estrutura do Projeto

- `main.py`: Código principal contendo a definição do problema (`SentinelaEstuarino`), a lógica do ambiente e a execução do agente.
- `aima-python/`: Submódulo contendo a biblioteca de algoritmos de IA (deve ser clonado).
- `README.md`: Documentação do projeto.

## 🧠 Algoritmos Utilizados

O agente utiliza busca heurística (A\*) para planejar o caminho, considerando:

- **Estado**: Localização (x, y), nível de bateria e alvos pendentes.
- **Ações**: Mover para CIMA, BAIXO, ESQUERDA ou DIREITA.
- **Objetivo**: Coletar todos os alvos e retornar à base com segurança.
