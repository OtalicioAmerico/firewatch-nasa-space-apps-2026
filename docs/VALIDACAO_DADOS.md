# Validação científica dos dados — Missão 01

Data da auditoria: 2026-11-14. Escopo: somente leitura. Nada foi adquirido, importado, migrado ou alterado
(Supabase, Hostinger, projeto legado e relatórios históricos intactos). O Supabase não foi consultado:
toda a verificação partiu dos CSV NASA preservados.

> **Aviso permanente.** Detecções FIRMS são *anomalias térmicas observadas por um sensor em uma passagem*.
> Não são incêndios confirmados, não são área queimada e não têm "% de certeza" aqui. Contagens de MODIS e
> VIIRS **não são equivalentes** entre si.

Rótulos: **VERIFICADO** = reproduzido nesta missão a partir dos dados NASA brutos; **OBSERVADO** = medido
nesta missão; **HIPÓTESE** = não testada; **REFERÊNCIA** = vem do legado e não foi reverificado.

## 0. Método da verificação independente
- Código novo (Python, só biblioteca padrão, sem instalar pacotes), escrito nesta missão; nenhum código do legado
  foi reutilizado. Os relatórios do legado serviram só como valores de referência para comparar.
- Leitura dos 111 CSV de `NASA_FIRMS` e `EVIDENCIAS\amostras_dimensionamento`: todos os SHA-256 conferem com
  `MANIFESTOS\SHA256SUMS.txt`.
- Brasil × vizinhos: ponto-em-polígono próprio sobre os biomas IBGE 2025 (Brasil terrestre) e, para Tocantins,
  sobre os 139 municípios IBGE 2025. Mesma fonte cartográfica (IBGE) do legado, implementação independente.
- Os scripts desta auditoria ficaram em diretório temporário da sessão (não versionados, para respeitar a
  "estrutura mínima"). Podem ser incorporados ao repositório na próxima missão, se a equipe quiser.

## 1. Inventário dos dados disponíveis
Retângulo de aquisição: `-74,-34,-34,6` (lon/lat), que inclui países vizinhos e oceano.

| Conjunto | Produto / satélite | Cobertura | Registros únicos |
|---|---|---|---|
| Lote 1 | MODIS_SP (Terra, Aqua) | **01–31/08/2025 e 01–31/08/2026**, diário contínuo | 2025: 50.023; 2026: 42.633 |
| Lote 2 | VIIRS_NOAA20_SP | 21–25/07/2025 | 21.827 |
| Lote 3 | MODIS_SP | 21–25/07/2025 e 21–25/07/2026 | 6.890 e 2.600 |
| Stage B | VIIRS_NOAA20_SP | 21–25/07/2026 (retângulo inteiro) | 11.255 |
| Stage B | sub-caixa `-60,-15,-50,-5` | NOAA-20/21/SNPP SP 25/07/2026; MODIS_SP 19–20/08/2026; NRT 06–09/11/2026 | ~1,3 mil só nessa sub-caixa |
| Amostras (EVIDENCIAS, **não importadas**) | MODIS_SP e NOAA-20_SP, retângulo inteiro | **dia 15 de cada mês**: MODIS 01/2025–08/2026 (20 dias), NOAA-20 SP 01/2025–07/2026 (19 dias); NRT (MODIS 15/09 e 15/10/2026; NOAA-20 15/08, 15/09, 15/10/2026); NOAA-21 e SNPP SP só 15/09/2025 | (ver §2.2) |

- **VERIFICADO:** a união deduplicada dos arquivos que alimentaram o banco tem **136.510** registros
  (MODIS_SP 102.146; NOAA-20 SP 33.082; NOAA-21 NRT 494 e SP 408; SNPP SP 351; MODIS_NRT 27; NOAA-20 NRT 2) e
  casa **1 para 1** com a extração do legado `_raw_export_lote3.tsv` (136.510 chaves satélite+instante+lat+lon;
  0 faltantes nos dois sentidos). Atenção: o banco **não contém** as amostras do dia 15.
- Sensores/satélites presentes: MODIS (Terra, Aqua); VIIRS 375 m (NOAA-20 em quantidade; NOAA-21 e SNPP em
  poucos dias).
- Disponibilidade NASA em 13/11/2026 (`availability-20261113.csv`): MODIS_SP 2000-11-01→2026-08-31;
  NOAA-20_SP 2018-04-01→2026-07-31; NOAA-21_SP 2023-03-01→2026-07-31; SNPP_SP 2012-01-20→2026-07-31; NRT cobre
  os meses seguintes. Há, portanto, **mudança SP→NRT** em 08/2026 (MODIS 09/2026) que precisa ser tratada.

## 2. Resultados das verificações independentes

### 2.1 Contagens de referência — VERIFICADO (idênticas)
| | 2025 | 2026 |
|---|---|---|
| MODIS_SP, retângulo, 21–25/07 | 6.890 | 2.600 |
| NOAA-20 SP, retângulo, 21–25/07 | 21.827 | 11.255 |
| MODIS dentro do Brasil (biomas IBGE) | 3.132 | 1.511 |
| NOAA-20 dentro do Brasil | 10.333 | 6.296 |

Classificação Brasil/vizinhos: os 136.510 registros dão 88.046 dentro do Brasil e 48.463 fora; **100 % de
concordância** com o status do legado (1 registro "Unresolved" na fronteira Paraguai/MS cai no Pantanal pelo
IBGE). Biomas coincidem em 100 %. Para Tocantins, o polígono municipal reproduz 100 % da atribuição de UF do
legado (10.194 registros). Pelas contagens acima, só 45–58 % (MODIS) e 47–56 % (NOAA-20) do retângulo é Brasil; o
resto é vizinho/oceano e **deve ser separado em qualquer indicador brasileiro**.

### 2.2 Dias com os dois sensores
- **29 dias** com MODIS_SP e NOAA-20_SP no retângulo: 21–25/07/2025, 21–25/07/2026 e os dias 15 de
  01/2025–07/2026 (19 dias; 10 + 19 = 29).
- **MODIS sem VIIRS:** 61 dias (todo 08/2025 e 08/2026, exceto o dia 15 de 08/2025 que tem VIIRS SP; 08/2026 não tem NOAA-20 SP, só NRT).
- **VIIRS sem MODIS:** nenhum dia com NOAA-20 SP. (NOAA-20 NRT existe em 15/08, 15/09 e 15/10/2026; os dois últimos têm MODIS NRT, 15/08 tem MODIS SP: produtos diferentes, não comparar sem marcar.)
- Todas as 27 UFs aparecem nos dois sensores nos dois anos (dentro do Brasil, 21–25/07).

### 2.3 Detecções por dia, sensor e território (21–25/07; retângulo, dentro do Brasil entre parênteses) — VERIFICADO
| Dia | Terra | Aqua | NOAA-20 |
|---|---|---|---|
| 2025-07-21 | 299 (161) | 754 (438) | 3.943 (1.957) |
| 2025-07-22 | 535 (214) | 976 (331) | 4.401 (2.209) |
| 2025-07-23 | 503 (166) | 644 (510) | 4.486 (2.198) |
| 2025-07-24 | 720 (298) | 897 (228) | 4.494 (1.857) |
| 2025-07-25 | 503 (276) | 1.059 (510) | 4.503 (2.112) |
| 2026-07-21 | 403 (217) | 327 (249) | 2.746 (1.424) |
| 2026-07-22 | 110 (30) | **32 (6)** | 2.169 (1.167) |
| 2026-07-23 | 253 (194) | 337 (316) | 1.794 (1.395) |
| 2026-07-24 | **79 (6)** | 355 (144) | 2.196 (1.160) |
| 2026-07-25 | 205 (119) | 499 (230) | 2.350 (1.150) |

### 2.4 Dia 22/07/2026 — OBSERVADO, não corrigido
Agrupando os instantes por passagem (lacuna > 30 min): em 22/07/2026 o Aqua tem **só duas passagens, ambas de
manhã (06:06 e 07:43 UTC)**, 32 detecções; a(s) passagem(ns) da tarde/noite (~18–20 UTC), que concentram o Aqua
nos outros dias, **não existem** nos dados. O NOAA-20 do mesmo dia está normal (6 agrupamentos, 2.169 pontos). Em
agosto de 2025 e 2026 (62 dias de MODIS) nenhum dia tem menos de 3 agrupamentos Aqua; logo 22/07/2026 é atípico
**nos dados**. No Tocantins: Aqua = **0**, NOAA-20 = 363, Terra = 16. O Terra de 24/07/2026 também está baixo
(79; sem a passagem diurna de ~12–13 UTC). **A causa continua não explicada** (HIPÓTESE: granulos/passagens
ausentes no produto, ou parada de instrumento; não verificável sem metadados de cobertura). Consequência
metodológica: *ausência de detecção ≠ ausência de atividade*; o indicador precisa de um estado "sem observação
conhecida" que hoje **não pode ser derivado** só das detecções (ver 4B).

### 2.5 Lacunas
- **Conhecidas:** NOAA-20 SP termina em 31/07/2026 e MODIS SP em 31/08/2026 (depois é NRT); NOAA-20 SP só tem 29
  dias úteis no retângulo; NOAA-21/SNPP: 1 dia (15/09/2025) em retângulo cheio + 25/07/2026 em sub-caixa.
- **Suspeitas:** passagem Aqua da tarde de 22/07/2026; passagem diurna do Terra em 24/07/2026; 21/07/2026 tem
  só uma passagem Aqua (19:13 UTC). Há dias de 08/2026 com 3 agrupamentos Aqua (sem passagem extra), compatível
  com variação normal de sobreposição de faixas.
- **Desconhecidas:** cobertura real (faixa/swath) por passagem, nuvens, ângulo de visada. As detecções FIRMS
  não carregam "onde o sensor olhou e não viu nada".
- Variabilidade diária: em 08/2025 o total diário MODIS no retângulo tem CV 0,43 (481–3.581) e em 08/2026 0,45
  (397–2.773). **Um único dia por mês (amostras do dia 15) é uma amostra muito ruidosa** do mês.

### 2.6 Diferença de horário Aqua / Terra / NOAA-20 — VERIFICADO
Pares ≤ 1 km, Δt = MODIS − NOAA-20, ±6 h, classes de 30 min:
- **Aqua:** 2025 7.975 pares, classe modal +90…+120 min (2.427); 2026 2.216 pares, modal +90…+120 (920).
- **Terra:** 2025 7.128 pares, modal −270…−240 (2.176); 2026 2.373 pares, modal −270…−240 (796).
Interpretação: o Aqua observa o mesmo lugar ~1–2,5 h **depois** do NOAA-20 (comparação útil, janela de ~60–150 min);
o Terra, ~3,5–5 h **antes**: as proximidades Terra×NOAA-20 refletem **persistência no mesmo local**, não observação
simultânea, e não devem alimentar pares "um incêndio visto duas vezes". Os números coincidem com o legado.

### 2.7 Comparação de detecções individuais (Aqua × NOAA-20) — VERIFICADO
Janela **escolhida apenas com 2025** (+60…+150 min) e aplicada a 2026 (teste fora da amostra). Candidato =
algum pixel NOAA-20 a ≤ R na janela. Acaso = NOAA-20 deslocado 0,3° (média de N/S/L/O), mesma janela.

| Ano | R | Aqua com candidato | Acaso | Razão obs/acaso |
|---|---|---|---|---|
| 2025 (n=4.330) | 500 m | 961 (22,2 %) | 0,12 % | 183 |
| 2025 | 1 km | 1.589 (36,7 %) | 0,36 % | 103 |
| 2025 | 3 km | 2.042 (47,2 %) | 1,96 % | 24 |
| 2026 (n=1.550) | 500 m | 265 (17,1 %) | 0,15 % | 118 |
| 2026 | 1 km | 456 (29,4 %) | 0,34 % | 87 |
| 2026 | 3 km | 610 (39,4 %) | 1,40 % | 28 |

- Relações em componentes conexos (Aqua×NOAA-20, janela acima). 500 m: 2025 1:1=420, 1:N=493, M:N=22, N:1=1; 2026 1:1=124, 1:N=129,
  M:N=5. 1 km: 2025 1:1=200, 1:N=358, M:N=343; 3 km: M:N domina (429 de 856 em 2025). **1:1 é minoria; 1:N é o
  padrão** (pixel MODIS de ~1 km cobre vários pixels VIIRS de 375 m: scan/track medianos 1,3/1,2 km vs
  0,42/0,45 km).
- Sensibilidade ao tempo (500 m, Aqua): |Δt| ≤ 60 min casa 10,3 % (2025) e 1,1 % (2026); ≤ 120 min, 26,5 % e 17,1 %.
  Janelas curtas não servem para MODIS×VIIRS.
- Variação por dia (Aqua, 1 km, janela): 2025 33/14/32/69/36 %; 2026 24/6*/38/10/42 % (*22/07, n=32).
  A taxa depende da sobreposição de faixas daquele dia, que **não está nos dados**.
- **Teto de referência (VIIRS×VIIRS, 25/07/2026, sub-caixa):** mesmo com satélites do mesmo instrumento e Δt de
  15–45 min, NOAA-20×NOAA-21 casa 51 % (375 m) / 71 % (750 m), NOAA-20×SNPP 59 % / 73 %, NOAA-21×SNPP 17 % / 23 %;
  1:1 continua minoria. Ou seja, correspondência ponto a ponto tem teto baixo mesmo no melhor caso.
- Limite: os 22 % não são "% de acerto": parte dos Aqua sem par está fora da faixa NOAA-20 daquela hora.

## 3. Capacidade A, B e C

### A. Comparação de detecções individuais — **possível como candidatos, não como pares validados**
Distância, tempo e candidatos funcionam para **Aqua × NOAA-20** (acima do acaso em ~24–180×). Faltam revisão humana,
geometria de faixa e pixels de referência independentes. Terra não entra. Relações 1:N/M:N devem ser mostradas
como tais.

### B. Harmonização para o calendário — **viável como método experimental, por presença, não por contagem**
Presença de atividade por célula-dia, medida mesmo dia UTC (MODIS = Terra+Aqua; VIIRS = NOAA-20), Jaccard contra nulo:

| Célula | 2025 Jaccard (nulo) | MODIS com VIIRS | 2026 Jaccard (nulo) | MODIS com VIIRS |
|---|---|---|---|---|
| 0,1° | 0,217 (0,024) | 59 % | 0,164 (0,013) | 53 % |
| 0,25° | 0,255 (0,084) | 66 % | 0,185 (0,043) | 58 % |
| 0,5° | 0,319 (0,226) | 75 % | 0,223 (0,143) | 66 % |
| 1,0° | 0,443 (0,411) | 87 % | 0,301 (0,267) | 78 % |

- A concordância é muito acima do acaso em 0,1–0,25° e **colapsa para o acaso em ≥ 0,5–1°** (o nulo de 0,3° não
  é um controle independente nessas escalas). A célula **0,25°** equilibra poder de discriminação e cobertura;
  0,5–1° dá números bonitos que **não distinguem** concordância de acaso.
- A assimetria é grande: o VIIRS ocupa 2–3× mais células que o MODIS (375 m vs 1 km), por isso soma ou média de
  contagens é inválida. **Não há constante de conversão**: razão NOAA-20/MODIS no Brasil, 3,3 em 2025 e 4,2 em 2026;
  por UF de 0,8 a 7,4.
- Indicador relativo por sensor: variação 2025→2026 no Brasil, 21–25/07: MODIS −51,8 %, NOAA-20 −39,1 %; sem
  22/07 nos dois anos: −43,0 % e −36,9 %. O sinal concorda; a magnitude difere ~6 pontos.
- Ranking por UF: Spearman 0,971 (2025) e 0,945 (2026) (legado: 0,969/0,946; diferença só de tratamento de empates).
- Estados do indicador (a implementar): *ambos*, *só MODIS*, *só VIIRS*, *nenhum detectado*, *sem observação*
  (esta última exige metadado de cobertura que **não temos**, hoje só heurística por passagens).

### C. Análise histórica — **insuficiente com os dados atuais**
- Comparação entre anos: só 2 janelas de 5 dias (julho) e 1 mês MODIS-only (agosto) e 7 meses (jan–jul) com 1 dia por mês.
  No dia 15 de jan–jul, MODIS e NOAA-20 **concordam no sinal da variação 2025→2026 em 7 de 7 meses**
  (MODIS +80, −16, −65, +66, −74, −27, −57 %; NOAA-20 +32, −44, −28, +37, −53, −26, −62 %, no Brasil), mas as magnitudes oscilam
  muito porque cada mês é **uma** amostra diária.
- Sazonalidade: perfil mensal (dia 15, Brasil) tem Spearman 0,942 entre MODIS e NOAA-20 (19 meses, n pequeno) e a
  estação seca (ago–nov) aparece nos dois. É indício, não resultado.
- Períodos anômalos/críticos: **não identificáveis**; sem linha de base multianual, não há "anômalo" nem "crítico".
  Só há 1 dia com defeito claro de cobertura (22/07/2026).
- A linha de base de um calendário histórico exige **vários anos contínuos**; o legado tem 2 anos, 1 mês e amostras.

## 4. Recorte recomendado: **Tocantins (UF 17)**
Critérios fixados antes de olhar o resultado: (i) muitas detecções nos dois sensores nos **dois** anos; (ii) o
maior número de dias com os dois sensores presentes; (iii) estado único, sem contaminação por vizinhos; (iv)
taxa de candidatos estável entre anos. Ranking dos estados por menor contagem Aqua entre 2025 e 2026 (dias de 10 com
≥ 5 detecções de Aqua e de NOAA-20):

| UF | Aqua 25/26 | NOAA-20 25/26 | cand. 1 km Aqua 25/26 | dias ok |
|---|---|---|---|---|
| **TO** | **205 / 306** | 1.085 / 2.080 | 33 % / 29 % | **9** |
| MT | 170 / 139 | 875 / 874 | 39 % / 31 % | 9 |
| PA | 161 / 97 | 733 / 565 | 21 % / 27 % | 9 |
| MG | 141 / 74 | 746 / 480 | 11 % / 39 % | 8 |
| MA | 232 / 69 | 1.353 / 473 | 33 % / 13 % | 8 |

- TO é o único que fica no topo nos dois anos, sem queda abrupta de amostra entre eles (MA, PI e RO caem ≥ 70 % de 2025 para 2026).
  AM, RO e PI ficam com n muito pequeno de Aqua em 2026. Mato Grosso é a segunda opção (também aceitável).
- TO sozinho: 18.986 registros do retângulo; 9 dos 10 dias com ambos os sensores; no mês de agosto, **MODIS contínuo
  em 62 dias** (3.127 em 2025 e 3.083 em 2026; nenhum dia < 10 registros) como série extra só-MODIS.
- Em TO (janela Aqua×NOAA-20, 10 dias): candidatos a 500 m 15,1 % (2025) e 17,3 % (2026); a 1 km 33,2 % e 29,4 %.
  Componentes 500 m: 1:1 = 15/23, 1:N = 12/30 (2025/2026): existem exclusivos e candidatos.
- Célula-dia em TO (28 dias com ambos): 0,25° → Jaccard 0,347 contra nulo 0,100; 0,1° → 0,270 contra 0,027;
  MODIS com VIIRS na célula 70 % (0,25°). Há **exclusivos dos dois lados** (244 células só MODIS, 814 só VIIRS em 0,25°).
- Dados auxiliares em TO: dias 15 de maio–nov 2025 têm NOAA-20 de 237 a 1.073 detecções; de dez/2025 a mar/2026
  quase nada (3–16): o calendário mostrará "sem detecção" em meses sem dados; **isso é o comportamento certo**.
- Limitações do recorte: TO tem mais Terra/Aqua fora de fase com NOAA-20; 22/07/2026 tem Aqua = 0 (usar como
  caso-teste de "sem observação conhecida", sem corrigir); o N20 de 08/2026 só existe como NRT.
- **Por que não escolher "o que dá melhor visual":** não foi usado critério de aparência; a razão de candidatos de
  TO (29–33 %) é próxima da média nacional (29–37 %).

## 5. Indicador experimental viável de testar
**Presença térmica por célula-dia e por sensor**, em células de **0,25°** (referência; 0,1° como detalhe), dia UTC,
no recorte TO (e, depois, Brasil):

1. Para cada célula e dia, `MODIS = 1` se Terra ou Aqua tem ≥ 1 detecção na célula; `VIIRS = 1` idem com NOAA-20
   (e NOAA-21/SNPP quando houver).
2. **Estado conjunto:** `ambos` / `só_MODIS` / `só_VIIRS` / `nenhum` / `sem_observação_conhecida`.
3. **Intensidade relativa** *por sensor*: índice = valor do dia ÷ mediana do próprio sensor na mesma região e janela
   sazonal (nunca soma, nunca conversão de escala).
4. Ao tocar uma célula-dia, listar as detecções que a sustentam (satélite, instante UTC, FRP, confiança bruta,
   candidatos Aqua×NOAA-20 se existirem). Proveniência: arquivo, SHA-256 e linha.

### 5.1 O que o indicador representa
- Presença/ausência de **anomalia térmica detectada** por MODIS e/ou VIIRS na célula, naquele dia UTC, e a concordância
  entre sensores; uma medida *relativa* de atividade por sensor ao longo do tempo.

### 5.2 O que NÃO representa
- Número de incêndios, área queimada, intensidade comparável entre sensores, certeza ou probabilidade de fogo.
- Ausência de fogo: "nenhum" pode ser nuvem, fora da faixa ou passagem faltante.
- Correspondência de eventos (os candidatos Aqua×NOAA-20 não são pares validados; Terra é persistência).
- Confiança unificada: FRP e confiança MODIS (0–100) e VIIRS (`l/n/h`; no NOAA-20 SP: n 78.573, l 7.711, h 5.065) não são
  equivalentes e não são mapeadas entre si; as classes VIIRS **não** são monótonas quanto à chance de par.

## 6. O que os dados permitem demonstrar hoje
- Calendário de células-dia de TO com estados `ambos/só MODIS/só VIIRS`, para **~29 dias** (10 contínuos em julho +
  amostras do dia 15) e, para o MODIS, **62 dias contínuos de agosto**.
- Candidatos Aqua×NOAA-20 com distância, Δt e taxa contra o acaso, explicados como candidatos.
- Comparação 2025×2026 lado a lado por sensor (índice relativo), com e sem 22/07.
- Caso de "dado insuficiente": 22/07/2026 (Aqua=0).
- Quanto ao Brasil inteiro: contexto nacional em 27 UFs para os 10 dias.

## 7. Requisitos do desafio ainda não atendidos
Fonte: página oficial do desafio, que não pôde ser aberta nesta sessão (falha de certificado TLS); a leitura abaixo
parte do enunciado resumido pela equipe e **deve ser conferida contra a página oficial** antes de qualquer promessa.
- Calendário **histórico** (vários anos) com comparação entre anos e períodos críticos: não atendido.
- Harmonização MODIS×VIIRS **validada** (exige revisão humana de pares, geometria de faixa e evidência independente):
  não atendida; só experimental.
- Selecionar região e período para qualquer área e data: só TO nos poucos dias disponíveis.
- Interface: não iniciada (por decisão desta missão).
- Repositório público na submissão: pendente (hoje local; remoto privado ainda não criado).

## 8. Dados adicionais mínimos (não adquiridos nesta missão)
Sem aquisição, ficamos em prova de conceito. Para um calendário histórico minimamente credível **em TO**:

| Item | Proposta | Volume / custo (estimativa) |
|---|---|---|
| Sensores | MODIS_SP (Terra+Aqua) e VIIRS_NOAA20_SP; NOAA-21_SP opcional (desde 03/2023) | — |
| Caixa | TO: `-51,-13.5,-45.5,-5` | ~1/9 da área do Brasil |
| Período mínimo | 01/01/2023 → 31/07/2026 do NOAA-20 SP e 01/2023 → 08/2026 do MODIS SP (~3,6 anos) | ~1.300 dias |
| Transações | ~2 por dia-unidade (medido nos lotes 1–3 com a caixa do Brasil) × 1.300 × 2 produtos ≈ **5.200** em ~520 requisições de 5 dias; limite 5.000 por 10 min | confirmar o custo da caixa menor com **uma** requisição antes |
| Linhas | MODIS TO ~30 mil/ano; NOAA-20 TO ~100–150 mil/ano (extrapolado de amostras diárias, ±50 %) → ~0,5 milhão | CSV bruto ~40 MB |
| Armazenamento | No legado ~1,45 KB/linha no banco: ~0,7 GB, **não cabe** nos ~182 MiB livres (217,4 de 400 MiB) | |

Recomendação de armazenamento: **não importar detecções novas no Supabase.** Processar fora do banco e guardar
só o agregado por célula-dia-sensor (esparso, dezenas de MB) e, para o recorte de demonstração, as detecções que
sustentam o calendário. (ESTIMATIVA, não observada.)
Alternativa ainda menor: 2025-01-01→2025-12-31 apenas (~1/3 do custo), só mostra um ciclo sazonal, não comparação de anos.
Também é útil, a baixo custo: NOAA-21_SP e SNPP_SP nos mesmos dias de julho de 2025/2026 (≈ 20 transações por requisição)
para outra passagem VIIRS e validação cruzada; BA_MODIS/BA_VIIRS (área queimada) como evidência independente.

## 9. Riscos científicos e limitações
1. **Prazo e proveniência:** o hackathon é 14–15/11/2026 (FAQ oficial, via busca; a página do desafio não abriu).
   Os dados foram adquiridos e a pesquisa preliminar feita em 13/11/2026, **antes** do início; isso deve constar
   como material anterior (ver `PROVENIENCIA.md`). Restam ~2 dias.
2. Poucos dias: 10 contínuos + 19 amostras; nenhuma conclusão sobre clima ou tendência.
3. Janelas de tempo escolhidas em dados; mitigado aqui por seleção só em 2025 e teste em 2026.
4. Sem geometria de faixa/ângulo de visada/nuvem: "sem detecção" é ambíguo.
5. Pixels diferentes (1 km × 375 m): contagens não comparáveis; razão VIIRS/MODIS varia no espaço e no tempo.
6. Fronteira Brasil: biomas IBGE excluem mar; pontos costeiros podem cair fora; vizinhos contaminam estados de fronteira.
7. SP×NRT: produtos diferentes; misturar sem marcar distorce.
8. Nulo por deslocamento de 0,3°: bom em 0,1–0,25°, **fraco** em ≥ 0,5° (fogo é agrupado).
9. Amostras do dia 15 não estão no banco e não são representativas do mês (CV diário ~0,4).
10. Correlação alta entre UFs (0,95–0,97) vem em parte de tamanho/vegetação das UFs; não prova equivalência.
11. Esta auditoria usou IBGE como no legado (mesma fonte cartográfica); a independência é de implementação, não de fonte.

## 10. Recomendação para a próxima missão
**Missão 02 — motor experimental mínimo, sem interface:** um script/biblioteca reprodutível (nada de telas) que, a
partir dos CSV preservados, gera para **Tocantins** a tabela célula-dia-sensor (0,25° e 0,1°), os estados
`ambos/só MODIS/só VIIRS/nenhum/sem observação`, o índice relativo por sensor, os candidatos Aqua×NOAA-20 e um
arquivo de proveniência por linha; com testes (reprodução dos números desta auditoria como teste de regressão) e o
dia 22/07/2026 como caso-teste. Só depois, interface mínima sobre esse arquivo.
Em paralelo: (a) a equipe (David e Tony) confere a página oficial do desafio e fecha os requisitos; (b) decide se
adquire o conjunto mínimo da seção 8 (autorização explícita), começando por **uma** requisição-sonda para medir o custo.

## Veredito
- **Prova de conceito (método experimental de calendário por presença, em TO): SUFICIENTE COM RESTRIÇÕES.**
  Suficiente para demonstrar o método, candidatos Aqua×NOAA-20, estados do indicador e o tratamento de "dado
  insuficiente". Restrições: ~29 dias, só dia UTC, só Aqua×NOAA-20, candidatos não validados, sem metadado de cobertura.
- **Análise histórica exigida pelo desafio: INSUFICIENTE** com os dados atuais; precisa de série multianual contínua.
