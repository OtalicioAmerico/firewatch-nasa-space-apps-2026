# Método de harmonização experimental MODIS × VIIRS (Missão 02)

> **Status: EXPERIMENTAL e NÃO VALIDADO.** Nada aqui foi validado contra evidência independente (revisão humana,
> área queimada, imagem). Detecções FIRMS são anomalias térmicas, não incêndios confirmados.

Rótulos usados nos documentos da Missão 02:

| Rótulo | Significado |
|---|---|
| **OBSERVADO** | medido nos dados NASA preservados nesta missão, reprodutível pelo código |
| **EXPERIMENTAL** | definição/parâmetro que escolhemos para testar; não é padrão científico |
| **HIPÓTESE** | explicação plausível, não testada |
| **NÃO VALIDADO** | resultado que depende de método ainda sem validação independente |

Código: `firecal/` (somente biblioteca padrão, sem interface). Execução: `python -m firecal run --config
config/poc_tocantins.json --data-dir <dados NASA> --out resultados/missao02`.

## 1. Unidade geográfica (EXPERIMENTAL)
Célula de **0,25° × 0,25°** (≈ 27 km de lado, ≈ 700 km²), grade ancorada em (0°, 0°): a célula (i, j) cobre
latitudes `[i·s, (i+1)·s)` e longitudes `[j·s, (j+1)·s)`. O tamanho é **parâmetro** (`celulas.principal`); 0,1° e 0,5°
são rodados como sensibilidade. A Missão 01 mostrou concordância muito acima do acaso em 0,1–0,25° e quase igual ao
acaso em ≥ 0,5°; 0,25° é, portanto, uma escolha de trabalho, **não uma escala validada**.
A região (ex.: Tocantins) é a união dos municípios IBGE 2025; uma detecção pertence à região se o ponto cai no
polígono. Células de fronteira ficam com detecções só da parte interna e são marcadas
(`celula_inteira_na_regiao = False`).

## 2. Unidade temporal (EXPERIMENTAL)
**Dia UTC**, a coluna `acq_date` do FIRMS. Não é dia local (Brasil está em UTC−3 a −5: passagens noturnas locais caem em
dias UTC diferentes das diurnas do mesmo "dia local"). Sem janela deslizante.

## 3. O que é "detectar atividade" numa célula-dia
`presença_MODIS(c, d) = 1` se há **≥ 1** detecção Terra **ou** Aqua na célula `c` no dia UTC `d`.
`presença_VIIRS(c, d) = 1` se há **≥ 1** detecção NOAA-20 (e, se configurados, NOAA-21/SNPP). Não há limiar de FRP nem de
confiança. Presença é **binária**: uma célula com 1 detecção e outra com 200 valem o mesmo (limitação; ver
`RESULTADOS_MISSAO_02.md`, §6). Contagens por satélite são gravadas como **informação descritiva**.

## 4. Como MODIS e VIIRS entram
Cada sensor entra **separadamente**, por seu próprio conjunto de células `M(d)` e `V(d)`. Não se converte um no outro,
não se usa fator fixo e não se mapeia a confiança numérica do MODIS (0–100) para a categórica do VIIRS (`l/n/h`).
O Terra é incluído em `M`, mas observa o local 3,5–5 h *antes* do NOAA-20 (Missão 01): seu acordo com o VIIRS é
persistência no local, não simultaneidade. Por isso a análise de candidatas individuais usa **só Aqua**.

## 5. Evitar somas duplicadas
1. **Entre arquivos:** detecções idênticas (mesmo satélite, instante, lat, lon a 5 casas) são unidas **antes** de qualquer
   contagem (`records.deduplicate`); os dois arquivos NOAA-20 de 2026 usados aqui são byte a byte idênticos
   (mesmo SHA-256) e os 11.255 registros duplicados são removidos; a origem das cópias fica em `refs`.
2. **Entre sensores:** nenhum indicador soma contagens MODIS e VIIRS. Os indicadores conjuntos são **operações de
   conjunto sobre células** (união, interseção); uma célula presente nos dois sensores conta **uma** vez na união.
3. Teste automatizado: `tests/test_harmonize.py::TestSemSomasDuplicadas`.

## 6. Observações exclusivas
Para o dia comparável: `SO_MODIS = M \ V` e `SO_VIIRS = V \ M` (células com atividade registrada por um sensor e **sem
registro** no outro). **Exclusiva ≠ "o outro sensor não viu"**: pode ser outra passagem, outra faixa, nuvem, 375 m × 1 km
ou ausência de dados. Em dia **não comparável** (§7) o estado é `MODIS_SEM_COMPARACAO` / `VIIRS_SEM_COMPARACAO`: a
detecção é registrada, mas não se afirma exclusividade.

## 7. Falta de cobertura e dados insuficientes
O que sabemos: quantas detecções cada satélite tem por dia. **Não sabemos** onde cada sensor olhou: sem faixa (swath),
sem máscara de nuvem, sem flag de completude, e nenhuma passagem é inventada. Por isso:

* Ausência de detecção numa célula-dia **nunca** é "sem fogo" nem "observado sem fogo". O estado é
  `SEM_DETECCAO_REGISTRADA` (dia comparável) ou `COBERTURA_INDETERMINADA` (dia não comparável).
  `SEM_DETECCAO_REGISTRADA` quer dizer só "nenhum registro", **sem** provar observação. Na tabela de saída essas células
  são implícitas (só há linhas para células com ≥ 1 detecção); o universo de células é informado à parte.
* **Status de satélite-dia** (`firecal/coverage.py`, EXPERIMENTAL, NÃO VALIDADO):
  * `SEM_DADOS`: nenhuma detecção do satélite naquele dia na janela de aquisição carregada;
  * `VOLUME_BAIXO`: detecções do dia < `min_ratio` (padrão 0,25) × mediana do **mesmo satélite** nos dias do mesmo ano do
    período (inclui dias com zero). É sinal estatístico de dado/passagem ausente, **não prova**;
  * `OK`: nenhum dos dois. **Não significa cobertura completa.**
* **Dia comparável** = todos os satélites requeridos (`Terra`, `Aqua`, `N20`) com status `OK`. O limiar foi **escolhido
  depois de observar 22/07/2026** (pós-hoc); a sensibilidade está em `resumo.json` (0,1 e 0,25 sinalizam só
  Aqua 22/07/2026; 0,4 e 0,5 sinalizam também Terra 24/07/2026; 0,6 sinaliza 4 satélite-dias).
* O status usa a **janela de aquisição inteira** (retângulo do Brasil), não só a região; não detecta, p. ex., o Terra de
  24/07/2026 ter 0 registros em Tocantins com status `OK` (79 no retângulo).

## 8. O que o indicador significa e não significa
**Significa:** em cada célula-dia da região, se algum sensor registrou anomalia térmica e se os dois sensores concordam
no local; quantas células têm atividade registrada por sensor; um índice relativo de cada sensor contra a própria
mediana; e quais dias não são comparáveis.
**Não significa:** nº de incêndios, intensidade, área queimada, "fogo confirmado", probabilidade, certeza, ausência de
fogo, nem equivalência entre contagens MODIS e VIIRS.

## 9. Definições matemáticas
Para um dia comparável `d`, região com `N` células e `M(d)`, `V(d)` ⊂ células:

* `A_M = |M|`, `A_V = |V|`, `A_∩ = |M ∩ V|`, `A_∪ = |M ∪ V|`, `SO_M = |M \ V|`, `SO_V = |V \ M|`.
* **Concordância espacial** `K(d) = A_∩ / A_∪` (Jaccard); indefinida se `A_∪ = 0`.
* **Controle de acaso** `K_nulo(d)`: Jaccard com as presenças VIIRS recalculadas após deslocar cada detecção VIIRS em ±0,3°
  (N, S, L, O), média das quatro. Bom discriminador em 0,1–0,25°; **fraco em ≥ 0,5°** (a atividade é agrupada).
* Referência de independência: `E[A_∩] = A_M · A_V / N` (só referência; atividade agrupada gera `lift = A_∩ / E > 1`).
* **Índice relativo por sensor** `I_M(d) = A_M(d) / med_M`, `I_V(d) = A_V(d) / med_V`, onde `med_s` é a mediana de `A_s`
  nos **dias comparáveis do período**. Indefinido se o dia não é comparável ou `med_s = 0`.
* **Indicador conjunto experimental** `R(d) = (I_M(d) + I_V(d)) / 2` — média de dois índices adimensionais, **nunca**
  soma de contagens; indefinido (`None`) se algum índice o for.
* Estado por célula-dia (§6–7): `AMBOS`, `SO_MODIS`, `SO_VIIRS`, `MODIS_SEM_COMPARACAO`, `VIIRS_SEM_COMPARACAO`,
  `SEM_DETECCAO_REGISTRADA`, `COBERTURA_INDETERMINADA`.

## 10. Correspondências individuais (CANDIDATA)
Módulo `firecal/matching.py`. Entre detecções **Aqua** (na região) e **NOAA-20** (toda a janela, para não truncar na
borda): par candidato se `dist ≤ raio` (haversine) e `tmin ≤ t_MODIS − t_VIIRS ≤ tmax`. Parâmetros EXPERIMENTAIS e
configuráveis: raios 500 m, 1 km, 3 km; janela +60…+150 min (derivada só de 2025 na Missão 01 e aplicada a 2026).
Relações por componentes conexos: 1:1, 1:N, N:1, M:N. Todo par traz as referências `arquivo:linha` dos dois
registros, distância e Δt. Rótulo fixo **CANDIDATA**; **não há probabilidade, % de certeza individual nem validação**.
Controle de acaso: VIIRS deslocado 0,3°. Os resultados da Missão 01 foram usados **só como regressão**.

## 11. Rastreabilidade
Cada detecção tem `rid = <arquivo relativo>:<linha do CSV>`; `evidencia_registros.csv` lista, por detecção na região, todas
as origens; `manifesto_execucao.json` guarda a configuração, os SHA-256 dos arquivos de entrada e das saídas.
Os CSV de entrada são verificados por SHA-256 e número de linhas antes do uso.

## 12. Parâmetros experimentais (todos NÃO VALIDADOS)
`celulas.principal` (0,25°), `cobertura.min_ratio` (0,25), `correspondencia.raios_m`, `correspondencia.janela_min`
(60–150), `nulo_deslocamento_graus` (0,3). Mudanças devem ser registradas em `docs/DECISOES.md`.
