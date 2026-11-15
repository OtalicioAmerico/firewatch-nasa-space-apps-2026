# Resultado da aquisição histórica 2021–2025 (Missão 04, Etapa 1)

Data: 2026-11-14. Detecção térmica FIRMS não é incêndio confirmado; **ausência de registro não é ausência de fogo** nem prova de observação.
Rótulos: **OBSERVADO** (medido nesta missão), **HIPÓTESE**, **EXPERIMENTAL / NÃO VALIDADO**. O indicador combinado `R` **não** foi reintroduzido.
Sem commit, sem escrita no Supabase, sem NOAA-21/SNPP, sem Etapa 2 (2019–2020). Dados, SQLite e manifestos estão **fora do Git**.

**Escopo cumprido:** Tocantins, caixa `-51.0,-13.75,-45.5,-4.9`, 2021-01-01 a 2025-12-31 (1.826 dias), `MODIS_SP` e `VIIRS_NOAA20_SP`. **732 de 732 janelas adquiridas e verificadas; nenhuma exceção.**
Nota: o `AGENTS.md` citado na missão **não existe** neste repositório; foram lidos `SECURITY.md` (global) e os documentos das Missões 01–03.

## 1. Preparação (verificada antes da execução)
- Disponibilidade NASA (API `data_availability`, 2026-11-14; custo 5 transações): `MODIS_SP` 2000-11-01→2026-08-31; `VIIRS_NOAA20_SP` 2018-04-01→2026-07-31. O período 2021–2025 está inteiro dentro dos dois intervalos.
- Chave (`FIRMS_MAP_KEY`, escopo do usuário): autenticação OK; cota inicial 12/5.000 (restos da janela anterior). Nunca impressa; URLs com chave nunca registradas (testado).
- Espaço: 143 GB livres (C:). Integridade dos dados anteriores: 9 arquivos da sondagem 03.1 e 6 da 03.2 com SHA-256 conferido, 0 divergências.
- Diretórios fora do Git: `aquisicao_historica_2021_2025/` (CSV originais + manifesto), `banco_pesquisa/` (`bruto_2021_2025.db`, `resultados_2021_2025.db`, `saidas/`), `cobertura_cmr/`.

## 2. Aquisição
Adquiridor novo (`tools/aquisicao/historico_firms.py`, 16 testes): janelas de ≤ 5 dias, contíguas e sem sobreposição (01/01/2021 com 1 dia + 365 janelas de 5 dias por produto = 366 por produto, **732 no total**),
processamento por produto/ano/mês, manifesto com HTTP, produto, período, linhas, bytes, ms, versões, SHA-256; checkpoints persistentes e retomada sem repetição; arquivos gravados **somente leitura** e nunca sobrescritos;
janela deslizante de 10 min com teto local de 3.000 transações (60 % do limite), 3 fluxos; verificação de custo contra o contador NASA a cada 25 requisições; parada em HTTP ≠ 200, corpo inesperado, falha de validação, divergência de custo ou 429 persistente.

| Item | Resultado |
|---|---|
| Requisições concluídas | **732 / 732** (HTTP 200 em todas; 0 repetições; 0 respostas 429) |
| Executadas na NASA | **730** |
| **Reutilizadas** | **2**: `MODIS_SP` e `VIIRS_NOAA20_SP` de 10–14/08/2022 (Missão 03.1), mesmo produto, caixa, data inicial e 5 dias; SHA-256 conferido; registradas com `origem = reutilizado` e arquivo de origem |
| Transações consumidas (esta execução, medidas) | **7.284** = 3.642 dias-unidade × 2 (730 requisições); sem divergência de custo nos controles (limite local de 100) |
| Autorizado | ≤ 732 requisições, ≤ 7.304 transações (as 20 transações das duas janelas reaproveitadas não foram gastas) |
| Duração | ~22 min de relógio, incluindo pausas do limitador (teto local); latência por requisição: mediana 1,12 s, média 1,64 s, máxima 26,5 s |
| Cota NASA ao final | 1.920/5.000 na janela corrente (limite não aproximado) |
| Bytes | 93.857.059 (≈ 89,5 MiB); 81,3 B/linha |

## 3. Arquivos, proveniência e integridade (OBSERVADO)
- **732 entradas no manifesto** (`manifesto_historico.jsonl`; SHA-256 do manifesto `d58d4fe7667ae58435e34cac1ea5169077e821825a5df9350bee2e69f789d377`), **732 arquivos no disco**, os 732 com SHA-256 igual ao manifesto, todos **somente leitura**.
- **731 SHA-256 distintos**: duas respostas só com cabeçalho (0 linhas) são idênticas — `MODIS_SP` 16–20/02/2021 e 11–15/01/2025 — e, por isso, só um arquivo vazio consta em `arquivo_origem` (a chave é o SHA-256). As duas janelas continuam no manifesto.
- Validação por resposta: produto/período, cabeçalho e campos obrigatórios, coordenadas dentro da caixa, datas dentro da janela, horas válidas, satélites esperados (`Terra`/`Aqua` para MODIS, `N20` para VIIRS), valores numéricos, duplicatas no arquivo, `version` registrada. **Rejeições: 0. Duplicatas dentro de arquivos: 0. Duplicatas entre arquivos: 0.**
- Janelas vazias (0 linhas) **não** são tratadas como "sem fogo".

## 4. Detecções por produto e ano (caixa inteira; Tocantins = polígono IBGE, `em_regiao`)
| Produto | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|
| MODIS_SP Aqua | 21.347 | 28.017 | 22.060 | 36.067 | 24.633 | 132.124 |
| MODIS_SP Terra | 17.014 | 21.381 | 18.980 | 26.692 | 18.549 | 102.616 |
| **MODIS_SP total** | 38.361 | 49.398 | 41.040 | 62.759 | 43.182 | **234.740** |
| **VIIRS_NOAA20_SP** | 150.464 | 209.989 | 147.319 | 241.677 | 170.743 | **920.192** |
| **Total** | | | | | | **1.154.932** |
Dentro de Tocantins (polígono): **602.856** (52 %); fora (estados/países vizinhos na caixa): 552.076. Previsão da sondagem: 0,7–1,6 M (central 1,1 M) — dentro da faixa.
(O manifesto soma por ano de **início da janela**; as janelas que cruzam a virada do ano deslocam algumas linhas entre anos — p. ex. MODIS 2022 = 49.405 no manifesto e 49.398 por data de detecção. O banco usa a data de cada detecção e tem **0 duplicatas**.)
Distribuição mensal em Tocantins (MODIS = Terra+Aqua | NOAA-20), 2021·2022·2023·2024·2025:

| Mês | MODIS | NOAA-20 |
|---|---|---|
| Jan | 192·108·78·95·36 | 658·327·223·315·175 |
| Fev | 68·122·180·184·107 | 92·157·513·270·289 |
| Mar | 136·97·138·328·179 | 205·143·104·312·385 |
| Abr | 186·333·360·173·171 | 397·1.158·793·467·410 |
| Mai | 1.406·1.835·1.506·2.329·1.946 | 4.235·4.922·4.267·6.818·5.814 |
| Jun | 1.949·2.526·2.659·3.515·2.336 | 5.881·8.430·7.867·10.600·6.731 |
| Jul | 3.176·3.249·2.969·3.487·2.580 | 11.431·11.416·8.587·11.144·8.966 |
| Ago | 5.477·5.137·2.127·6.086·3.127 | 23.138·20.133·8.930·27.035·14.621 |
| Set | 4.799·6.359·5.586·13.497·5.896 | 20.344·25.364·23.527·57.696·26.904 |
| Out | 2.383·4.193·2.477·3.083·5.808 | 10.827·29.342·10.579·11.256·26.801 |
| Nov | 190·345·1.492·769·1.477 | 618·1.639·5.301·2.360·5.099 |
| Dez | 55·134·719·359·182 | 163·410·1.987·996·788 |
Sazonalidade clara (seca mai–out); a atividade varia muito entre anos (set/2024 NOAA-20 57.696 contra 20.344–26.904 nos outros; ago/2023 8.930 contra 14.621–27.035). **Não** foi investigada a causa das diferenças (clima, observação, coleção).

## 5. Versões (OBSERVADO)
| Produto / satélite | `version` | Registros | Primeiro dia | Último dia |
|---|---|---|---|---|
| MODIS_SP Aqua | **6.03** | 49.364 | 2021-01-01 | 2022-12-28 |
| MODIS_SP Aqua | **61.03** | 82.760 | 2023-01-01 | 2025-12-31 |
| MODIS_SP Terra | **6.03** | 38.395 | 2021-01-01 | 2022-12-31 |
| MODIS_SP Terra | **61.03** | 64.221 | 2023-01-01 | 2025-12-31 |
| VIIRS_NOAA20_SP N20 | **2** | 920.192 | 2021-01-01 | 2025-12-31 |
- **Transição MODIS determinada:** **entre 2022-12-31 (último dia 6.03) e 2023-01-01 (primeiro dia 61.03), exatamente na virada do ano, para Terra e Aqua.** Nenhum dia tem as duas versões. Cada ano tem uma só versão (HIPÓTESE: o arquivo Standard foi produzido em blocos anuais; não confirmado).
- 6.03 = bloco A (provável Collection 6), 61.03 = bloco B (provável Collection 6.1): **inferência, não confirmada** (`mapa_versao.confirmada = 0`). O valor literal é preservado em `versao_bruta`.
- **VIIRS:** `version = 2` em todos os anos. **Isso não prova homogeneidade científica** (calibração/algoritmo podem mudar sem mudar o campo).
- **Mudança na série perto da transição (OBSERVADO, exploratório):** razões de detecções Aqua/NOAA-20 e Terra/NOAA-20 em Tocantins por trimestre:

| | Aqua/N20 T2 | T3 | T4 | Terra/N20 T2 | T3 | T4 |
|---|---|---|---|---|---|---|
| 2021 (6.03) | 0,206 | 0,132 | 0,134 | 0,130 | 0,113 | 0,092 |
| 2022 (6.03) | 0,189 | 0,137 | 0,102 | 0,134 | 0,122 | 0,047* |
| 2023 (61.03) | 0,183 | 0,145 | 0,123 | 0,167 | 0,115 | 0,140 |
| 2024 (61.03) | 0,197 | 0,136 | 0,160 | 0,139 | 0,105 | 0,128 |
| 2025 (61.03) | 0,204 | 0,126 | 0,122 | 0,140 | 0,104 | 0,107 |
  \*T4/2022 do Terra tem **13 dias (11–23/10/2022) sem nenhum dado Terra** (ver §9). Nos trimestres de maior atividade (T2, T3) a razão Aqua/N20 é **estável** entre blocos (T3: 0,132–0,137 em A; 0,126–0,145 em B), sem degrau visível;
  o Terra/N20 em T3 é ~0,11–0,12 em A e ~0,10–0,115 em B (queda possível de ~5–10 %, dentro da oscilação interanual). **Isto não exclui efeito de coleção** (resolução baixa, 1 região, razões por trimestre) **nem o atribui**: não se isola deriva, coleção e atividade.

## 6. Banco SQLite (OBSERVADO)
- `bruto_2021_2025.db`: **326.201.344 bytes (311 MiB)** para 1.154.932 detecções = **282 B/linha**, incluindo tabela de origens (1.154.932 vínculos detecção↔arquivo↔linha) e 3 índices. `resultados_2021_2025.db` (derivados, reconstruível): **8,7 MB**.
- Esquema: `arquivo_origem` (SHA-256, produto, período, bytes, linhas, versões), `deteccao` (satélite, instante UTC, dia, lat, lon, FRP, confiança, scan, track, dia/noite, `versao_bruta`, `colecao_inferida`, `em_regiao`, célula 0,25°; **chave única** satélite+instante+lat+lon), `deteccao_origem`, `mapa_versao`, `execucao_import`; índices por data+satélite, data+célula e satélite+versão.
- **Importação:** 731 arquivos novos (+1 já importado por SHA idêntico), 1.154.932 linhas lidas, 1.154.932 novas, 0 duplicatas, **180 s** (inclui ponto-em-polígono do Tocantins). **Idempotente:** uma segunda execução leu 732 entradas, importou 0 e levou 2 s. Verificação: 0 detecções sem origem; 0 arquivos com contagem divergente.
- Processamento inicial (agregações e correspondência por dia): **15 s**. Consultas por data/satélite/célula em milissegundos. Código em `firecal/store.py` (6 testes) e `tools/historico/` (importar, processar, cobertura CMR).

## 7. Dias sem registro e dias com ambos os sensores (OBSERVADO; **ausência ≠ sem fogo**)
- **Caixa inteira** (1.826 dias): NOAA-20 sem registro em **84** dias; Aqua em **285**; Terra em **356**; MODIS (Terra+Aqua) em **155**; dias com MODIS e NOAA-20: **1.639**; só MODIS: 32; só VIIRS: 103; **nenhum dos três: 52** (concentrados em fev–mar e dez–jan).
- **Tocantins** (polígono; categorias de registro, não de fogo): 

| Ano | ambos | só VIIRS | só MODIS | nenhum registro |
|---|---|---|---|---|
| 2021 | 273 | 52 | 6 | 34 |
| 2022 | 289 | 38 | 7 | 31 |
| 2023 | 312 | 27 | 13 | 13 |
| 2024 | 307 | 28 | 11 | 20 |
| 2025 | 301 | 36 | 8 | 20 |
  Total: 1.482 dias com os dois, 181 só VIIRS, 45 só MODIS, 118 sem registro. Os dias "sem registro" caem quase sempre na estação úmida (jan–mar, dez); a cobertura CMR abaixo mostra que **a maioria deles tem cobertura geométrica do satélite**, isto é, não são dias sem observação conhecida.

## 8. Extensão e intensidade, separadas (Tocantins, células de 0,25°; OBSERVADO)
Extensão = células com ≥ 1 detecção no dia (mediana diária); intensidade = detecções por célula ativa (mediana diária). Não há soma entre sensores nem `R`.

| Ano | MODIS: detecções · células/dia · det/célula | VIIRS: detecções · células/dia · det/célula |
|---|---|---|
| 2021 | 20.017 · 10 · 2,00 | 77.989 · 22 · 2,70 |
| 2022 | 24.438 · 13 · 2,00 | 103.441 · 37 · 2,89 |
| 2023 | 20.291 · 16 · 1,89 | 72.678 · 38 · 2,81 |
| 2024 | 33.905 · 16,5 · 2,13 | 129.269 · 39,5 · 3,24 |
| 2025 | 23.845 · 13 · 2,00 | 96.983 · 30 · 3,33 |
VIIRS ocupa ~2–3× mais células por dia que o MODIS e tem intensidade ligeiramente maior; **as contagens absolutas dos dois sensores não são comparáveis**. A extensão MODIS depende da cobertura (ver §9: o Aqua cobre a região só em parte em ~29 % dos dias).

## 9. Cobertura geométrica CMR (processada para todo o período; EXPERIMENTAL / NÃO VALIDADA)
Consultados os grânulos L2 (`MYD14`, `MOD14`, `VJ114IMG`) que tocam a caixa em cada um dos 1.826 dias: **5.478 consultas, 0 falhas**, sem custo de transação FIRMS. Estado por satélite-dia sobre as 364 células de Tocantins (centro dentro do polígono):

| Satélite | Cobertura total | **Parcial** | Sem grânulo no catálogo |
|---|---|---|---|
| NOAA-20 | 1.823 | 0 | **3** (30/09/2023; 04–05/02/2024) |
| Aqua | 1.275 | **536** (29 %; fração mediana coberta 0,76; mínima 0,29) | **15** (01–15/04/2022) |
| Terra | 1.805 | 5 | **16** (11–23/10/2022; 13–15/05/2025) |
- **Consistência FIRMS × CMR:** todos os registros do Aqua em Tocantins (68.321) e quase todos do NOAA-20 (480.359 de 480.360) caem em grânulo do mesmo satélite no horário (±1 min) e dentro do polígono; **Terra: 161 de 54.175 (0,3 %) sem grânulo**.
- **Limite do catálogo (CORREÇÃO):** em **13–15/05/2025 o CMR `LPCLOUD` não tem grânulo Terra, mas a FIRMS tem 72, 30 e 58 detecções Terra na caixa (65, 21, 41 em Tocantins)**; esses são 127 dos 161 casos. Logo, **"sem grânulo" no CMR não prova ausência de observação**; vale como sinal a confirmar. Já em 01–15/04/2022 (Aqua) e 11–23/10/2022 (Terra) **os dois lados coincidem**: nenhum grânulo e **0 registros FIRMS** (13 e 15 dias).
- **Dias sem registro em Tocantins × estado CMR:** NOAA-20 163 dias sem registro — 160 com cobertura geométrica total e 3 sem grânulo; Aqua 463 — 225 total, 223 parcial, 15 sem grânulo; Terra 510 — 494 total, 3 parcial, 13 sem grânulo.
  **Cobertura geométrica sem detecção não é "sem fogo"** (nuvem, fumaça, ângulo e condição de queima desconhecidos); **"sem grânulo" não é "sem fogo"**; "parcial" significa que parte da região não foi vista.
- **Pendente de cobertura:** máscara de nuvem/qualidade, ângulo de visada, validação do polígono plano contra pixels, tratamento dos 536 dias de Aqua parcial para normalizar extensão por **células cobertas**, e confirmar com a NASA os casos "sem grânulo".

## 10. Diferenças temporais e espaciais (OBSERVADO)
- **Hora UTC mediana das detecções diurnas em Tocantins:** Aqua 16,87 → 16,95 → 17,15 → 17,57 → **18,13** h (2021→2025); Terra 13,63 → 13,45 → 13,22 → 12,92 → **12,34** h; NOAA-20 estável (16,75 · 16,73 · 16,83 · 16,80 · 16,72). **A deriva do Aqua (+1,3 h) e do Terra (−1,3 h) é gradual; o NOAA-20 não deriva.**
- **Aqua com NOAA-20 a ≤ 1 km:** classe modal de Δt (Aqua − NOAA-20, ±6 h): 2021 +45/0/−30 min (larga); 2022 0; 2023 +15/−15/0 (muito estreita); 2024 +75 (e +15, 0); 2025 +60/+30/+75. Fração dos Aqua em Tocantins com um NOAA-20 a ≤ 1 km e |Δt| ≤ 15 min: **20,3 %, 24,3 %, 22,1 %, 15,2 %, 1,1 %**; ≤ 30 min: **43,9 %, 41,7 %, 37,5 %, 26,2 %, 3,6 %**; ≤ 60 min: 67,4 %, 68,4 %, 54,0 %, 42,1 %, 20,1 % (2021…2025).
- **Candidatas Aqua×NOAA-20 a ≤ 500 m (CANDIDATA; janela fixa |Δt| ≤ 30 min, controle por deslocamento 0,3°):** 28,2 % (acaso 0,1 %), 26,2 % (0,1 %), 22,4 % (0,1 %), 15,8 % (0,1 %), **2,0 %** (0,0 %) em 2021…2025. Com |Δt| ≤ 60 min: 42,8, 42,7, 32,0, 25,2, 11,8 %. Sem probabilidade individual; não são eventos confirmados.
- **Interpretação cautelosa:** a oportunidade de observação quase simultânea Aqua × NOAA-20 **desaba em 2025** e já cai em 2024; coincide com a deriva do horário do Aqua. As taxas por ano **não** podem ser atribuídas só à deriva (coleção A→B e atividade variam), mas a defasagem de horário é medida diretamente e independe da coleção.
- **Espacial:** Tocantins concentra 52 % das detecções da caixa; as células ativas por dia do VIIRS são ~2–3× as do MODIS; o Aqua cobre só parte da região em ~29 % dos dias (§9), o que reduz sua extensão aparente nesses dias.

## 11. Capacidade atual para produzir o calendário histórico
- **Sim, com restrições**: 5 anos contínuos (1.826 dias) de células-dia em Tocantins para MODIS (Aqua e Terra separados) e NOAA-20, proveniência por registro, versões e cobertura CMR por satélite-dia — suficiente para: extensão e intensidade por sensor, sazonalidade, comparação entre anos, concordância espacial `K` e exclusivas **somente em dias comparáveis** (cobertura total dos satélites requeridos), e candidatas Aqua×NOAA-20 por ano.
- **O que ainda não sustenta:** uma linha de base MODIS única 2021–2025 (versão muda em 2023; deriva do Aqua/Terra), anomalias estatisticamente fortes (5 anos), qualquer afirmação de ausência de fogo, e uma segunda região.
- **O que mudou em relação ao estudo anterior:** o catálogo CMR é útil, mas **incompleto** (Terra, mai/2025); a estimativa de volume (1,1 M) se confirmou; a taxa de candidatas **cai muito mais cedo do que se supunha** (já em 2024).

## 12. Riscos e pendências
1. Significado oficial de 6.03/61.03 ainda não confirmado; possíveis efeitos da recalibração L1B nas detecções do Terra (documentados, não quantificados).
2. Cobertura CMR: catálogo incompleto, polígono plano, sem nuvem; Aqua parcial em 29 % dos dias.
3. Sobreposição Aqua×NOAA-20 só até 2023–2024; o histórico de correspondência exige janela por ano, não herdada.
4. Uma única região; diferenças interanuais de atividade grandes (ago/2023 baixo; set/2024 muito alto) sem causa investigada.
5. Chave FIRMS ainda gravada em texto claro no registro do usuário (remover quando não for mais necessária).
6. Nada foi validado cientificamente; testes de software não substituem revisão por David e Tony.
7. `arquivo_origem` usa o SHA-256 como chave: arquivos de conteúdo idêntico colapsam (dois vazios); o manifesto preserva as duas janelas.

## 13. Recomendações para a próxima missão (sem iniciá-la)
1. **Rodar o motor `firecal` sobre o SQLite** (adaptar entrada) para 2021–2025 em Tocantins: extensão e intensidade por sensor, estados de cobertura por **CMR** (`SEM_OBSERVACAO_CONHECIDA`, `PASSAGEM_PARCIAL`, `COBERTURA_GEOMETRICA_SEM_DETECCAO`, `DETECCAO_REGISTRADA`) e concordância apenas em dias comparáveis; **extensão normalizada por células cobertas**.
2. **Referência histórica separada por bloco MODIS** (A: 2021–2022; B: 2023–2025) e o **NOAA-20 como série contínua**; repetir o teste da razão MODIS/NOAA-20 com mais anos (se a Etapa 2 for autorizada, 2019–2020 amplia o bloco A).
3. **Correspondência por ano:** janelas e raios estimados em cada ano; relatar 2021–2023 (alta oportunidade) e 2024–2025 (baixa) separadamente; não usar `|Δt| ≤ 30 min` fixo para 2025.
4. Pedir à NASA/FIRMS a definição de `version` (6.03/61.03) e a explicação dos dias "sem grânulo" (Terra 2025-05-13..15).
5. Decidir Etapa 2 (2019–2020; `MODIS_SP` + `VIIRS_NOAA20_SP`, 2.924 transações) **depois** de rever este relatório; **não iniciada**.
6. Planejar a exportação seletiva para o Supabase (esquema isolado) a partir do banco `resultados`.
7. Remover a chave do registro do usuário ao concluir as aquisições.
