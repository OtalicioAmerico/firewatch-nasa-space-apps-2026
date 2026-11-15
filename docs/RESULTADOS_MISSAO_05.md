# Resultados da Missão 05 — processamento histórico e calendário harmonizado (Tocantins, 2021–2025)

Data: 2026-11-14. Detecção térmica FIRMS não é incêndio confirmado nem área queimada. **Ausência de registro não é ausência de fogo.**
Rótulos: **OBSERVADO** (medido nos dados), **EXPERIMENTAL** (regra nossa), **HIPÓTESE**, **NÃO VALIDADO**. O indicador combinado `R` **não** foi recriado.
Nenhuma aquisição NASA, nenhuma escrita no Supabase, nenhum commit. Banco SQLite, saídas e caches ficam **fora do Git** (`<local folder, not published>`).

**Resumo honesto.** O calendário real foi produzido e é reprodutível (bit a bit). Os cenários de cobertura conservador (A) e exploratório (B) quase não diferem, porque as regras de corroboração raramente atuam sobre estes dados.
O ganho mensurável da harmonização está em (i) separar **extensão** de **intensidade**, o que muda a leitura de ~20 % das semanas frente à contagem bruta; (ii) **bloquear K em dias não comparáveis**. A concordância K existe acima do acaso (≈ 3–5×), mas depende do nível de atividade e **não** melhora a informação além dos indicadores por sensor.
A referência histórica com 5 anos é fraca (MODIS por bloco tem só 1–2 anos de referência). **Nada aqui está validado cientificamente**; 147 testes de software aprovados só mostram que o código faz o que está definido.

## 1. Verificação inicial (OBSERVADO)
- Documentos lidos: `METODO_HARMONIZACAO`, `RESULTADOS_MISSAO_02`, `ESTUDO_MELHOR_PERIODO`, `VERIFICACAO_VERSOES_MODIS`, `RESULTADO_AQUISICAO_HISTORICA_2021_2025`, `README` e `SECURITY.md` (global). (`AGENTS.md` não existe.)
- **1.154.932 detecções únicas; 602.856 em Tocantins** — iguais ao relatório da aquisição. `pragma integrity_check = ok`; 0 detecções sem origem.
- **732 arquivos de origem** (731 SHA-256 distintos): todos com SHA-256 igual ao manifesto, todos somente leitura.
- **Testes:** os 100 testes do estado anterior tinham passado ao fim da Missão 04 (não reexecutados no início; nenhum valor divergiu); agora são **147** (47 novos), **147 aprovados** com os dados e 28 pulados sem eles.
- Nenhum valor divergiu; nada precisou ser investigado antes de processar.

## 2. Interpretação da cobertura (CMR não é autoridade absoluta)
### 2.1 Regras fixadas **antes** de ver os resultados (`firecal/cobertura.py`, `firecal/calendario.py`)
| Regra | Valor |
|---|---|
| Fração coberta de uma célula | fração da **área** da célula dentro da união dos polígonos dos grânulos, por amostragem 5×5 (atalho: 5 pontos todos dentro = 1, todos fora = 0; aproximação documentada) — **não** o centro da célula |
| Teste de pertinência | **esférico** (arestas = círculos máximos; os 5.478 sat-dias têm 0 grânulos não convexos). O teste plano usado na Missão 04 e o esférico dão os mesmos 161 + 1 conflitos |
| `COBERTURA_GEOMETRICA_CORROBORADA` | fração ≥ 0,95 **e** catálogo completo no dia **e** sem conflito FIRMS×CMR no satélite-dia |
| Catálogo completo (evidência independente) | contagem **global** de grânulos do dia ≥ 85 % da mediana do satélite no período (consultada ao CMR: 3.285 + 2.193 contagens globais) |
| `COBERTURA_GEOMETRICA_PARCIAL` | 0 < fração < 0,95, catálogo completo, sem conflito |
| `CONFLITO_FIRMS_CMR` | ≥ 1 detecção FIRMS em Tocantins que **não** cai em nenhum grânulo (tempo ±1 min e polígono) naquele satélite-dia |
| `COBERTURA_INDETERMINADA` | conflito no dia **ou** catálogo sem evidência de completude (sempre prevalece sobre "sem grânulo") |
| `SEM_COBERTURA_GEOMETRICA_CORROBORADA` (estado adicional) | fração = 0 com catálogo completo e sem conflito (não é "sem fogo"; é só "o catálogo, completo no dia, não tem grânulo cobrindo") |
| Detecção | `DETECCAO_REGISTRADA` (≥ 1 registro) / `AUSENCIA_DE_DETECCAO_REGISTRADA` — **dimensão separada** da cobertura |
| Comparável (K) | ≥ 80 % do universo coberto/corroborado por **ambos** os sensores |
| Dia válido no cenário A | ≥ 50 % do universo corroborado; semana só tem valor com ≥ 4 dias válidos; referência exige ≥ 2 anos |
Universo: **433 células** de 0,25° (364 com centro no polígono IBGE de Tocantins + 69 de fronteira com detecção registrada no território). As células de fronteira têm parte fora do estado; a fração coberta refere-se à célula inteira.

### 2.2 Cenários de sensibilidade
- **A — conservador:** só células com cobertura CORROBORADA entram (numerador e denominador); casos inconclusivos são **excluídos explicitamente** e as detecções excluídas são contadas (`A_*_det_excluidas`).
- **B — exploratório:** todas as detecções entram; o denominador é Σ max(fração coberta, 1 se houve detecção) (uma detecção prova observação da célula); incertezas ficam sinalizadas (`*_cel_cobertura_desconhecida`, estados de cobertura).

### 2.3 Resultado das regras (OBSERVADO, 1.826 dias × 3 satélites)
| | Aqua | Terra | NOAA-20 |
|---|---|---|---|
| Catálogo incompleto (dias) | 24 | 29 | 8 |
| `CONFLITO_FIRMS_CMR` (dias / registros) | 0 / 0 | **4 / 161** (13–16/05/2025) | 1 / 1 (29/06/2024) |
| Dias com cobertura parcial em alguma célula | 561 | 4 | 0 |
| Dias com fração coberta média < 0,95 | 470 (26 %; 472 sem arredondar) | 21 | 3 |
| Estado dominante do dia (CORROBORADA / INDETERMINADA / SEM corroborada / CONFLITO) | 1.760 / 24 / 42 / 0 | 1.794 / 25 / 3 / 4 | 1.817 / 8 / 0 / 1 |
- **Impacto A × B:** dias inválidos no cenário A: Aqua 98, Terra 32, NOAA-20 9; família MODIS 1 dia; família VIIRS 9 dias (**3 com detecções, 685 detecções excluídas**: 29/09/2023, 01/10/2023, 29/06/2024). Classificação semanal diferente em **1 de 265** semanas (VIIRS 2024, semana 26); mensal: 0; K diferente em 7 dias. **Conclusão: o resultado é robusto à escolha A/B; as regras de cobertura raramente atuam.**
- O conflito 13–16/05/2025 (Terra) reproduz o achado da Missão 04: a FIRMS tem 65, 21, 41 e 34 detecções Terra em Tocantins e o CMR não tem os grânulos; ficam `COBERTURA_INDETERMINADA` (não "sem observação").
- Cobertura geométrica **não** garante visibilidade: nuvem, fumaça e ângulo de visada seguem desconhecidos e nenhuma máscara foi usada.

## 3. Processamento 2021–2025 (OBSERVADO)
- Total processado: **1.154.932 detecções** (602.856 em Tocantins: MODIS 122.496 [Terra 54.175 + Aqua 68.321] e NOAA-20 480.360).
- **Células-dia com detecção** (Tocantins, 0,25°): **136.519** por satélite-célula-dia; por família: MODIS **42.954**, NOAA-20 **85.193**. Dias: 1.826; semanas (blocos fixos de 7 dias, não ISO): 265; meses: 60.
- Por dia e sensor o calendário contém: contagens por satélite; extensão (células ativas) e **numerador e denominador** da normalização; detecções por célula ativa; fração coberta, estados e conflitos por satélite; versão e bloco MODIS; arquivos de origem (SHA-256, 12 caracteres); células com cobertura desconhecida; K e K do acaso; defasagem de horário.
- **Grandeza produzida (exata):** `ext_norm = células com ≥ 1 detecção ÷ denominador de cobertura` — fração do **universo observado** com atividade **registrada** no dia, por sensor; `intens = detecções ÷ células ativas`. Não é área queimada, não é número de incêndios.
  Cenário A: denominador = células corroboradas; cenário B: Σ max(f, 1[detecção]) (≈ 433 quando a cobertura é total).

## 4. Indicadores históricos por sensor (medianas diárias; cenário B; Tocantins)
| Ano | MODIS: células ativas · ext_norm · det/célula | VIIRS (NOAA-20): células ativas · ext_norm · det/célula |
|---|---|---|
| 2021 | 10 · 0,0231 · 2,00 | 22 · 0,0508 · 2,71 |
| 2022 | 13 · 0,0300 · 2,00 | 37 · 0,0854 · 2,89 |
| 2023 | 16 · 0,0369 · 1,90 | 38 · 0,0878 · 2,81 |
| 2024 | 16,5 · 0,0381 · 2,13 | 39,5 · 0,0924 · 3,24 |
| 2025 | 13 · 0,0300 · 2,00 | 30 · 0,0693 · 3,33 |
Cenário A: idêntico no MODIS e quase idêntico no VIIRS (p. ex. 2021 22,5 células, 0,0520). VIIRS ocupa ~2–3× mais células que o MODIS; as contagens dos dois sensores **não são comparáveis**.
Sazonalidade (mediana de ext_norm por mês, ver `calendario_mensal.csv`): atividade registrada concentrada em mai–out; **intensidade** (det/célula) sobe com a atividade (VIIRS jun–out: 5,0 no bloco A e 4,7 no B; MODIS 2,6 e 2,5).

## 5. Resultado da normalização por cobertura (OBSERVADO)
- **Família MODIS:** a cobertura da família é o melhor caso entre Terra e Aqua e o **Terra cobre quase sempre a região inteira**; por isso a normalização praticamente não altera o indicador (Spearman 1,00 entre extensão bruta e normalizada; difere em 4 dias).
- **Aqua isolado:** em **470 dias (26 %)** a fração coberta média é < 0,95 (mediana 0,70) e em 59 dias < 0,5. Nesses dias a extensão normalizada pela cobertura efetiva é, em mediana, **1,38×** a normalizada pelo universo inteiro. A extensão bruta do Aqua nos dias parciais é baixa (mediana 1 célula contra 10 nos dias de cobertura total), mas **não** se separa o efeito da cobertura do da sazonalidade (dias parciais ocorrem também na estação úmida).
- **Conclusão:** a normalização importa para o Aqua e para comparações Aqua × NOAA-20, não para o calendário da família MODIS; ela fica explícita (numerador e denominador) nas colunas `B_aqua_*`/`A_aqua_*`.

## 6. Diferenças entre os blocos MODIS (6.03 × 61.03) (OBSERVADO; sem atribuição de causa)
| Bloco | Período | MODIS ext_norm | MODIS det/célula | VIIRS ext_norm | VIIRS det/célula | razão de extensão MODIS/VIIRS |
|---|---|---|---|---|---|---|
| A (6.03) | jun–out 2021–2022 | 0,0924 | 2,63 | 0,1859 | 5,02 | 0,486 |
| B (61.03) | jun–out 2023–2025 | 0,0901 | 2,50 | 0,1848 | 4,70 | 0,488 |
Razão de extensão MODIS/VIIRS em jun–out por ano: **0,442, 0,514, 0,467, 0,525, 0,500** (2021…2025): **sem degrau visível na virada 2022→2023** (0,514→0,467→0,525). A intensidade cai ~5 % (MODIS) e ~6 % (VIIRS) do bloco A para o B: como o VIIRS (que não mudou de versão) cai igual, **não há indício de efeito específico da coleção**; o dado **não exclui** efeito pequeno nem o atribui (deriva, atividade e coleção variam juntas).
Referência MODIS por bloco: o bloco A tem só 2021–2022, logo **2021 e 2022 ficam `REFERENCIA_INSUFICIENTE`** para o MODIS (só há 1 outro ano no bloco); o bloco B tem 3 anos (referência de 2 anos por ano avaliado).

## 7. Concordância entre sensores (OBSERVADO; K = Jaccard sobre células comparáveis)
- Dias comparáveis: **1.810 (A) e 1.819 (B) de 1.826**. **K não aplicável em 131 (A) e 125 (B) dias**, quase todos "sem células ativas" (115/118) e 16/7 por "cobertura comparável insuficiente". Diagnósticos de K nesses dias estão **separados** em `diagnostico_K_dias_nao_comparaveis.csv` e **não** vão para a saída pública.
- **MODIS (Terra+Aqua) × NOAA-20, K mediano por ano (B) / controle de acaso:** 2021 0,196 / 0,039; 2022 0,250 / 0,059; 2023 0,224 / 0,051; 2024 0,228 / 0,057; 2025 0,214 / 0,043 (≈ 4–5× o acaso). Em jun–out: 0,33–0,39 (acaso 0,08–0,11). K_A e K_B praticamente iguais (Spearman 1,00).
- **Células MODIS ativas que também são ativas no NOAA-20:** mediana 0,67–0,74 (0,81–0,86 em jun–out); fração inversa (VIIRS→MODIS): 0,30–0,34. K é limitado pela assimetria de extensão (o VIIRS ocupa ~3× mais células), por isso a fração "MODIS confirmado pelo VIIRS" é mais interpretável que K.
- **Aqua × NOAA-20** (célula e dia): K mediano (A) 0,169 · 0,194 · 0,174 · 0,188 · 0,154 em 2021…2025 (acaso 0,03–0,04), com 288–296 dias comparáveis por ano. **K não depende da defasagem de horário**: Spearman −0,017 (n = 1.120); mediana por faixa de |defasagem|: ≤ 30 min 0,24; 30–90 min 0,21; > 90 min 0,21.
- **Defasagem de horário Aqua − NOAA-20** (mediana diária das detecções diurnas): **8, 13, 21, 41, 77 min** em 2021…2025 (CMR: início de grânulo mais próximo; ver coluna `dif_inicio_granulo_aqua_n20_min`).
- Cuidados: K cresce com a atividade (Spearman K×extensão: 0,84 MODIS, 0,70 VIIRS); em dias de contagem alta nos dois sensores K_B mediano é 0,45 (n = 347). **Concordância de células não é identidade de incêndios.**

## 8. Referência histórica e semanas/meses distintos (cenário B, extensão normalizada; referência **exclui sempre o ano avaliado**)
Classificação (sem teste de significância; só a faixa mín–máx dos anos de referência; ≥ 2 anos de referência; ≥ 4 dias válidos na semana):
| Ano | VIIRS (ref. = 4 outros anos): acima / dentro / abaixo | MODIS (ref. = mesmo bloco): acima / dentro / abaixo |
|---|---|---|
| 2021 | 8 / 26 / 18 | referência insuficiente (52 semanas) |
| 2022 | 11 / 35 / 6 | referência insuficiente |
| 2023 | 11 / 32 / 9 | 16 / 25 / 11 (ref. 2024–2025) |
| 2024 | 12 / 36 / 4 | 25 / 19 / 8 (ref. 2023–2025 sem 2024) |
| 2025 | 9 / 29 / 14 | 10 / 10 / 32 (ref. 2023–2024) |
- **2025 com referência só de anos anteriores (pedido da missão):** VIIRS (2021–2024): 9 acima, 29 dentro, 14 abaixo; MODIS no mesmo bloco (2023–2024, n = 2): 10 / 10 / 32; MODIS com todos os blocos (SENSIBILIDADE, 2021–2024): 5 / 35 / 12. **A conclusão para 2025 depende da referência** (n = 2 contra n = 4): 32 semanas "abaixo" no MODIS por bloco caem para 12 quando o bloco A entra. Não é leitura robusta.
- **Semanas em que os dois sensores estão acima da referência disponível:** 2023 (9 semanas, p. ex. 23 e 27 [jun–jul] e 38 [set]), **2024 (11, incluindo 36–37, primeira quinzena de setembro, o pico de atividade registrada da série)**, 2025 (6, p. ex. 43–44 e 46 [out–nov]). **Ambos abaixo:** 2023 (6, p. ex. 34–35 e 39–40 [ago–out]), 2024 (3), **2025 (12, p. ex. 22–23, 26–27, 30, 32–33, 38 e 41 [jun–out])**. Divergem (um acima, outro abaixo): 2 semanas (2023 s14 e 2025 s10).
- Concordância entre os dois sensores na classificação semanal de 2023–2025: igual em 91 semanas, diferente em 65 (MODIS usa referência de 2 anos).
- Meses (VIIRS): 2023 ago e jul abaixo, nov–dez acima; 2024 maio, jun, ago e set acima, abr e out abaixo; 2025 jan e set abaixo, mar acima, demais dentro. Expressão adotada: **"atividade registrada acima/abaixo da referência disponível"** (n = 4 anos, no máximo).
- **Não se afirma anomalia estatisticamente robusta** com cinco anos; as classes apenas descrevem a posição frente aos anos disponíveis.

## 9. O ganho da harmonização (a avaliação mais importante)
**A. Contagens brutas × B. indicadores por sensor × C. K e comparabilidade.**
1. **A → B (contagem × extensão/intensidade):** no nível diário o ordenamento quase não muda (Spearman contagem × extensão 0,99 MODIS e 0,98 VIIRS). **No nível semanal, a classificação frente à referência muda em 28 de 156 semanas (18 %) no MODIS e 58 de 260 (22 %) no VIIRS** quando se usa a extensão em vez da contagem. Exemplos reais:
   - **MODIS, semana 47/2023:** 163 detecções, **abaixo** da referência do mesmo bloco (173 em 2024, 168 em 2025); a **extensão** (0,0327) está **acima** da referência (0,0303 e 0,0284): atividade espalhada em mais células, com menos detecções por célula.
   - **VIIRS, semana 31/2021:** 3.138 detecções, **acima** do máximo da referência (3.013); a extensão (0,163) está **dentro** da faixa (0,122–0,194) e a intensidade é a maior (6,3 contra 4,6–6,6): "mais detecções" por maior intensidade nas mesmas células, não por maior extensão.
   Isto é um ganho **real e mensurável**, não artificial: duas leituras diferentes da mesma semana.
2. **Normalização por cobertura:** altera o Aqua em 26 % dos dias (×1,38 mediano), mas **não** o calendário da família MODIS (o Terra cobre). Não mudou nenhuma classificação semanal entre A e B (1 em 265).
3. **K e comparabilidade (C):**
   - O que **acrescenta**: bloqueia K em dias não comparáveis (16 dias A ou B, vários com conflito FIRMS×CMR ou catálogo incompleto, p. ex. 14/05/2025: Terra com 21 detecções sem grânulo no catálogo) e dá um "controle de acaso" (K ≈ 4–5× o acaso), mostrando que há concordância espacial real nos dias comparáveis.
   - O que **não acrescenta**: K depende da atividade e da assimetria de extensão (dias de pico: K 0,70–0,78 em set/2024; dias de pico no VIIRS com MODIS pouco ativo: K ≈ 0,18–0,22, perto do limite A_MODIS/A_VIIRS, p. ex. 08/10/2022: 40 células MODIS, 181 VIIRS, 33 em comum, K 0,18); não detecta a deriva do Aqua (K independente da defasagem); e não melhora a classificação semanal frente à referência (as classes MODIS e VIIRS concordam em 91 de 156 semanas).
   - **Avaliação:** a harmonização por **presença em célula-dia** é **robusta à deriva do horário** (K estável 2021–2025) enquanto a **correspondência ponto a ponto** não é (Missão 04: de 28 % para 2 %). Mas **o ganho de interpretação vem do passo B**; o passo C é, sobretudo, controle de qualidade e diagnóstico. **Não se cria indicador único.**
4. **Falha documentada:** os cenários de cobertura A/B quase não diferem; a harmonização por cobertura **não** muda a leitura do calendário MODIS; K não adiciona informação independente da extensão. O ganho justificável é: extensão × intensidade por sensor, flags de comparabilidade e proveniência.

## 10. Limitações
1. 5 anos; MODIS por bloco só 1–2 anos de referência; 2021–2022 sem referência MODIS no bloco A; 2025 muito sensível à referência.
2. Coleção MODIS não confirmada; deriva do Aqua/Terra e atividade variam junto com a coleção; nada é atribuído a uma só causa.
3. Cobertura CMR: catálogo incompleto (Terra 13–16/05/2025), polígono sem nuvem/ângulo, fração de área por amostragem, células de fronteira com parte fora do estado; "corroborada" **não** significa "céu limpo".
4. Presença binária por célula de 0,25° (≈ 700 km²) satura em dias muito ativos e ignora intensidade (por isso a intensidade é separada).
5. Semana = bloco fixo de 7 dias (não ISO); mês/semana incompletos têm menos dias válidos.
6. K sem identidade de incêndios; depende da atividade; K_nulo por deslocamento de 0,3° é razoável em 0,25°.
7. Uma região (Tocantins); sem validação independente (área queimada, imagens); sem revisão por David e Tony.
8. Os 147 testes provam o software, **não** a validade científica.

## 11. Prontidão para o calendário visual
**Pronto para alimentar uma interface de demonstração**, com condições:
- Arquivos reais: `calendario_diario.csv/json` (1.826 linhas, 122 colunas), `calendario_semanal.csv/json` (265), `calendario_mensal.csv/json` (60), `diagnostico_K_dias_nao_comparaveis.csv` (**não público**), `analise_m05.json` (resumos).
- A interface deve mostrar **separadamente** MODIS e NOAA-20 (extensão e intensidade), o estado de cobertura e conflitos, K **somente quando aplicável**, a classificação frente à referência com o n de anos, a versão/bloco MODIS e os arquivos de origem; usar sempre "atividade registrada" e nunca "fogo/ausência de fogo".
- Antes: decidir (i) como exibir a incerteza do MODIS por bloco; (ii) se o filtro de cobertura A ou B será o padrão (B recomendado, A como alternância); (iii) rótulos EXPERIMENTAL/NÃO VALIDADO visíveis; (iv) revisão humana de uma amostra de dias/semanas.

## 12. Precisa adquirir 2019–2020?
- **Não é necessário para construir o calendário visual** (os dados atuais já alimentam extensão, intensidade, cobertura, K e a referência de 4 anos do NOAA-20).
- **Seria útil/necessário se a equipe quiser** referência MODIS no bloco A para 2021–2022 (hoje inexistente) e ≥ 4 anos de referência por bloco: 2019–2020 (bloco A, 6.03) levaria o bloco A a 4 anos (2019–2022); o bloco B continuaria com 3 (2023–2025).
- Custo: **2.924 transações, 294 requisições** (MODIS + NOAA-20). Alternativa mais barata para engordar o bloco B: janeiro–agosto de 2026 já existem em Standard até 31/07 (NOAA-20) e 31/08 (MODIS), ≈ 910–972 transações, mas dão só 7–8 meses (as semanas de set–dez não teriam 2026).
- **Recomendação:** adiar a Etapa 2 até a interface demonstrar o calendário; adquirir 2019–2020 só se a equipe precisar de referência MODIS por bloco para a apresentação.

## 13. Arquivos produzidos (fora do Git, exceto o código)
`banco_pesquisa/saidas_m05/` (calendários, diagnósticos, análise), `banco_pesquisa/resultados_m05.db` (cobertura por sat-dia e universo), `cobertura_cmr/` (granulos 2021–2025, contagens globais). Código novo no repositório (sem commit): `firecal/cobertura.py`, `firecal/calendario.py`, `tools/historico/{cobertura_celulas,calendario,analise_m05}.py`, `tools/pesquisa/cmr_contagem_global.py`, testes `test_cobertura.py`, `test_calendario.py` (agregação, referência), `test_m05_real.py` (idempotência/reprodutibilidade/proveniência/versões/CMR incompleto/conflitos/K não aplicável/exclusão do ano avaliado), além de `test_store.py` (idempotência da importação, versão preservada).
