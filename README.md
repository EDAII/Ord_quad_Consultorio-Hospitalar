## Alunas  
| Matrícula | Nome |  
|-----------------------|---------------------|  
| 20/0025058 | Mayara Alves de Oliveira |  
| 20/2016720 | Luana Ribeiro Soares     |  

## Descrição do projeto
O OrdenaClinic é um sistema inteligente de organização e priorização de pacientes, desenvolvido para otimizar o fluxo de atendimento em ambientes hospitalares e unidades de pronto atendimento. Ele utiliza algoritmos de ordenação como base para estruturar uma fila de triagem mais ágil, estável e justa, garantindo que cada paciente seja atendido de acordo com o grau de urgência, respeitando também a ordem de chegada e outros critérios clínicos definidos pela instituição.

A proposta central é utilizar algoritmos de ordenação estáveis para preservar a ordem de chegada entre pacientes de mesma prioridade, enquanto algoritmos de maior desempenho podem ser aplicados em situações de grande volume, permitindo uma reorganização dinâmica da fila conforme novos pacientes são registrados.

### Regras de prioridade (baseadas no SUS)

O SUS prioriza o atendimento por meio de dois critérios principais: a classificação de risco, que prioriza casos de emergência e urgência (cores vermelho e amarelo, respectivamente), e a legislação de atendimento prioritário, que garante prioridade para grupos específicos (pessoas com deficiência, idosos, gestantes, lactantes e crianças de colo) em situações não urgentes. Em todos os casos, o atendimento de pacientes mais graves sempre tem precedência, independentemente do grupo de prioridade.

#### Classificação de Risco

É um sistema utilizado em hospitais e pronto-atendimentos para ordenar o fluxo de pacientes com base na gravidade da condição, geralmente representado por cores:

- Vermelho (Prioridade Zero): Emergência, com necessidade de atendimento imediato (risco de morte).
- Amarelo (Prioridade 1): Urgência, com necessidade de atendimento o mais rápido possível.
- Verde (Prioridade 2): Casos menos graves, sem risco imediato de vida.
- Azul (Prioridade 3): Baixa complexidade, atendidos de acordo com o horário de chegada.
- Branco (Administrativo): atendimentos administrativos / baixa prioridade

#### Atendimento Prioritário (Lei nº 10.048/2000)

Além da classificação de risco, a legislação brasileira garante prioridade no atendimento em filas para grupos específicos, mas essa prioridade não se sobrepõe a casos de emergência e urgência:

- Pessoas com deficiência
- Idosos com 60 anos ou mais
- Gestantes
- Lactantes
- Pessoas com crianças de colo
- Pessoas com obesidade (Lei nº 10.048/2000, com atualizações)

No OrdenaClinic usamos essas regras como critério secundário (aplicado quando a triagem clínica for equivalente), garantindo que casos mais graves continuem tendo precedência absoluta.

## Guia de instalação

### Requisitos

- Python 3.8+ instalado 

### Instalação das dependências

Instale as bibliotecas necessárias via pip (recomendado dentro de um ambiente virtual):

```powershell
python -m pip install pandas dash
```


### Executando a aplicação

Na pasta do projeto execute:

```powershell
python .\ordenaclinic_app.py
```

Depois abra no navegador o endereço mostrado no terminal.

Para interromper a aplicação: pressione Ctrl+C no terminal.

### Dicas e solução de problemas

- Se faltar algum pacote, instale com `python -m pip install <pacote>` (por ex. `pandas`, `dash`).
- Se receber erros de versão, crie um ambiente virtual com `python -m venv .venv` e ative-o antes de instalar as dependências.
## Capturas de tela
 
  ![Home](capturas/Home.PNG)  

## Conclusões

O OrdenaClinic demonstra como aplicar regras de prioridade clínica (triagem) e legislação de atendimento prioritário para organizar filas de atendimento de forma justa e estável. Utilizamos um algoritmo estável (Merge Sort) para preservar a ordem de chegada entre pacientes de mesma prioridade e adicionamos camadas de prioridade legal (idosos, gestantes, lactantes, pessoas com deficiência, crianças de colo e obesidade). A aplicação serve como protótipo pedagógico e base para futuras integrações em ambientes reais de saúde.

## Referências

- Lei nº 10.048/2000 — Prioridade de atendimento a alguns grupos (texto consolidado): https://www.planalto.gov.br/ccivil_03/leis/LEIS_10.048.htm
- Ministério da Saúde — Diretrizes e materiais sobre Classificação de Risco e acolhimento: https://www.gov.br/saude


