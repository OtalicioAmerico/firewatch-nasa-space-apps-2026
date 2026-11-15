# Verificação das versões MODIS_SP (Missão 03.2)

Data: 2026-11-14. Detecção térmica FIRMS não é incêndio confirmado. Rótulos: **OBSERVADO**, **NASA** (página oficial, com link), **HIPÓTESE**, **NÃO VALIDADO**.
Nenhum commit, deploy, migration ou escrita em Supabase; as 732 requisições do histórico **não** foram executadas.

## 1. Execução (6 requisições de 1 dia, 12 transações)
Chave: lida da variável de ambiente do usuário, nunca impressa; autenticação NASA OK; cota antes: 0/5.000; consumo medido: **12 transações (2 por requisição, igual ao previsto)**; cota depois: 12.
`MODIS_SP`, caixa de Tocantins `-51.0,-13.75,-45.5,-4.9`, **12/08 de cada ano de 2019 a 2024** (dia fixado antes da consulta, sem escolha por resultado). Saída fora do Git: `aquisicao_versoes_03_2/` (não sobrescreve `aquisicao_sondagem_03_1/`).

| Data | HTTP | Linhas | Bytes | ms | Transações | SHA-256 |
|---|---|---|---|---|---|---|
| 2019-08-12 | 200 | 309 | 24.763 | 973 | 2 | `6cbb2c59…30b2e8` (`6cbb2c598f10d9f55d4fb1e35cb2856a16ab7ae112f16bee7cde42e49330b2e8`) |
| 2020-08-12 | 200 | 222 | 17.795 | 1.059 | 2 | `36006e820441cce5284dfee166080fd9bf525ab839a9bb2f2f2b63ef43a98cbe` |
| 2021-08-12 | 200 | 221 | 17.711 | 1.055 | 2 | `03d2ea88ed1c6a451364df3525f6bb87cb82ce320e0c7fed6dc44213d301a8ee` |
| 2022-08-12 | 200 | 247 | 19.762 | 1.104 | 2 | `fad632c8dbc1872178cf91bbe47ca26e86f938c6fae7b90ea94400f04f1f179a` |
| 2023-08-12 | 200 | 181 | 14.857 | 871 | 2 | `55832c04e380fbece2ea8b84611ba85fc16b0ab9e90ceabb2fccdbc461be5e7c` |
| 2024-08-12 | 200 | 147 | 12.221 | 854 | 2 | `3c5f96e87156a06f29750d8a8804eaaf2f7669e62fcd1dbf24de22612496e43d` |
Reprodutibilidade: as 247 linhas de 12/08/2022 desta consulta são **idênticas** às mesmas 247 linhas já obtidas na Missão 03.1 (mesmas chaves e mesmos valores em todas as colunas).

## 2. Versões por ano e satélite (OBSERVADO)
Cada arquivo tem **uma única versão** (nenhum arquivo mistura valores); Terra e Aqua **sempre têm a mesma versão no mesmo dia**. Registros por ano/satélite (inclui as janelas de 10–14/08 de 2022 e 2025 e de 10–14/03/2025 da Missão 03.1):

| Ano (agosto) | `version` | Aqua | Terra | Fonte |
|---|---|---|---|---|
| 2019 | **6.03** | 161 | 148 | 1 dia (12/08) |
| 2020 | **6.03** | 110 | 112 | 1 dia |
| 2021 | **6.03** | 79 | 142 | 1 dia |
| 2022 | **6.03** | 1.015 | 604 | 12/08 + janela 10–14/08 |
| 2023 | **61.03** | 108 | 73 | 1 dia |
| 2024 | **61.03** | 97 | 50 | 1 dia |
| 2025 (mar. e ago.) | **61.03** | 60 + 276 | 17 + 190 | janelas 10–14/03 e 10–14/08 |
Também **61.03** em todas as amostras e lotes de 2025–2026 já preservados. VIIRS (NOAA-20 e SNPP): `version = 2` em todos os arquivos de 2022 e 2025.
**Transição aparente:** entre **14/08/2022** (último dia 6.03 visto) e **12/08/2023** (primeiro dia 61.03 visto); a data exata é **desconhecida** (janela de ~12 meses). Não há outra mudança entre 2019 e 2024.
**Atualização (Missão 04): a aquisição 2021–2025 datou a transição: último dia 6.03 = 2022-12-31 (Terra); primeiro dia 61.03 = 2023-01-01 (Terra e Aqua); nenhum dia com as duas versões.**
**Não foi possível localizar a data exata com as 6 requisições autorizadas**; ela sairá diretamente do campo `version` de cada linha na aquisição 2021–2025 (§6), sem requisições extras.

## 3. Evidências oficiais consultadas
- [FIRMS, atributos MODIS/VIIRS](https://earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs): `version` "identifica a coleção (ex.: MODIS Collection 6.1) e a fonte de processamento"; exemplos **6.1**, **6.1NRT**, **6.1RT**, **6.1URT**. **A página não cita 6.03 nem 61.03.**
- [FIRMS, MCD14DL NRT](https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/mcd14dl): "C61 não contém atualizações do algoritmo científico"; "as mudanças melhoram a abordagem de calibração na geração dos produtos MODIS **Level 1B** de Terra e Aqua"; "**Collection 61 substituiu a Collection 6 em abril de 2021**" (NRT).
  A página trata só do NRT e não diz se o arquivo Standard (MCD14ML) foi reprocessado.
- [LP DAAC/Earthdata, MOD14 v061](https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod14-061): L1B 6.1 inclui mudanças de **resposta × ângulo de varredura (RVS)** em bandas de reflectância de Aqua e Terra, **correção do "optical crosstalk" nas bandas infravermelhas do Terra**,
  correção da tabela de consulta ("forward LUT") do Terra para 2012–2017 e correção de polarização nas bandas solares; cobertura **2000-02-24 até o presente** (granulos L2, mesma coleção em todos os anos); a página não diz se há quebra para detecções.
- Guias [MODIS C6/C6.1 Fire User Guide](https://earthdata.nasa.gov/s3fs-public/2023-09/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf) e [MOD14 User Guide V61](https://LPDAAC.USGS.GOV/documents/1005/MOD14_User_Guide_V61.pdf): **encontrados, mas o texto não foi lido** (PDF sem extração disponível nesta máquina); a seção "Summary of Algorithm and Product Changes" deve ser lida pela equipe.
- Dentro dos dados: coluna `version`, CMR (granulos L2 `V061` para todos os anos, ver Missões 03/03.1).

## 4. Avaliação científica
**4.1 6.03 e 61.03 são coleções diferentes?** **Muito provável, não confirmado oficialmente.** (a) Os dois valores não aparecem na documentação da FIRMS; (b) a convenção documentada é "coleção + fonte" (6.1, 6.1NRT…); (c) a troca ocorre ao mesmo tempo em Terra e Aqua e é permanente (sem alternância em 2019–2024); (d) o prefixo 6 / 61 coincide com Collection 6 / Collection 61, e o sufixo `.03` é igual nos dois.
Não assumimos equivalência: tratamos **"6.03" como bloco A (provável Collection 6)** e **"61.03" como bloco B (provável Collection 6.1)** até confirmação por escrito da NASA (ex.: o guia do usuário ou o suporte FIRMS).

**4.2 Há mudanças de calibração capazes de afetar a comparabilidade?** **Sim, por documentação, mas sem magnitude conhecida.** Mudou a entrada (L1B), não o algoritmo. A correção de *crosstalk* nas bandas infravermelhas do Terra altera as temperaturas de brilho usadas pelo detector, logo
**pode** alterar limiares e contagens, sobretudo no Terra; as mudanças de RVS/polarização afetam bandas de reflectância usadas na máscara diurna. **Nada nas páginas lidas quantifica o efeito em detecções, FRP ou confiança.**

**4.3 Teste empírico preliminar (OBSERVADO, amostra pequena e confundida; NÃO conclusivo).** Medianas dia/noite por ano de temperatura de brilho e tamanho de pixel, bloco A × bloco B:
- Aqua, dia: BT31 308,6/308,4/303,9/308,0 (2019–2022) → 310,0/306,7/302,2 (2023–2025); BT21 333,6/332,9/326,2/331,8 → 333,6/334,1/325,6. **Sem degrau claro na fronteira**; variação de ±3–5 K ano a ano, do mesmo tamanho que a oscilação dentro de cada bloco.
- Terra, dia: BT31 306,5/303,7/306,9/303,5 → 303,0/302,6/299,3; BT21 327,2/322,5/328,7/324,4 → 322,5/324,1/316,0. **Tendência de queda de 2022 para 2025** (−4 K em BT31, −8 K em BT21), compatível com **três** explicações não separáveis aqui: mudança de coleção, deriva orbital/hora local do Terra
  (hora UTC mediana do Terra diurno cai de ~13,8–14,0 h para ~12,3 h) e sazonalidade/composição da amostra (1 dia/ano; n de 23 a 126). **Não** é possível atribuir.
- A proporção dia/noite e o tamanho de pixel (scan) mudam entre amostras; `scan` do Aqua diurno oscila de 1,1 a 2,3 sem padrão de bloco (depende de quais passagens caem na caixa).
- Todos os registros são tipo 0 (vegetação presumida). Colunas e unidades idênticas nos dois blocos.

**4.4 Como registrar versão e coleção no SQLite (proposta, EXPERIMENTAL):**
```
arquivo_origem(id, caminho, sha256, produto, ... )
deteccao_bruta(..., versao_bruta TEXT NOT NULL,         -- valor literal da coluna version ('6.03', '61.03', '2', ...)
                    colecao_inferida TEXT,               -- 'C6','C6.1','VIIRS-C2'; derivada da tabela abaixo
                    ...)
mapa_versao(produto, versao_bruta, colecao_inferida, confirmada INTEGER, fonte TEXT, observacao TEXT)
   ('MODIS_SP','6.03','C6',0,'inferido; nao consta na documentacao FIRMS',...)
   ('MODIS_SP','61.03','C6.1',0,'inferido; ...',...)
indice (satelite, versao_bruta, dia_utc)
```
A versão entra em **toda** tabela de resultado (`res_*` carrega `blocos_versao` do período agregado) e em um relatório de execução (distribuição de versões por mês).
Nenhuma linha é descartada ou "corrigida" por versão.

**4.5 Separar resultados por coleção ou aplicar ressalvas?**
- **Separar para tudo o que compara MODIS ao longo do tempo:** referência histórica (percentis semanais), anomalias, tendências e índices de **extensão/intensidade MODIS** devem ter base **por bloco** (A: ≤ 2022; B: ≥ 2023, conforme a data real) e **nunca** misturar bloco A e B numa única linha de base sem aviso.
  Comparar anos de blocos diferentes só com a ressalva "possível quebra de coleção (não quantificada)".
- **VIIRS é a série contínua de referência** (`version = 2` em todas as amostras; coleção única): serve para **testar a quebra do MODIS**, por exemplo com a razão mensal Aqua/NOAA-20 (mesmas células-dia) ao redor da transição; se houver degrau, é indício de efeito de coleção (ou de deriva); se não, a quebra é pequena frente à variabilidade.
- Para a **correspondência** MODIS×VIIRS e a **harmonização**: calcular taxas, janelas e concordância **por bloco** (e por ano), e comparar Aqua×NOAA-20 nos dois blocos; diferenças entre blocos **não** são atribuíveis só à coleção.

**4.6 Efeito na análise histórica e na harmonização com VIIRS.** A quebra possível fica **dentro** de 2021–2025 (A: 2021–2022; B: 2023–2025), que é exatamente a janela de aquisição; isso é útil (permite testar a quebra) e arriscado (a comparação MODIS 2022×2025 mistura coleção, deriva e atividade).
O calendário histórico por sensor deve exibir MODIS em dois blocos ou com marca de coleção; o índice **VIIRS** pode ser contínuo.

**4.7 A deriva orbital continua sustentada?** **Sim para o horário**, **não separada para as detecções.**
- **Horário** (independente da coleção): os grânulos L2 do CMR são de uma única coleção (`V061`, 2000–presente) e mostram a deriva do Aqua (Missão 03); nos dados FIRMS, a hora UTC mediana diurna do **Aqua** sobe de ~16,7 h (2019) para ~18,0 h (2025) e a do **Terra** cai de ~13,8–14,0 h para ~12,3 h,
  **de forma gradual e contínua**, sem salto coincidente com a troca 6.03→61.03. Hora de passagem não depende da coleção de processamento, portanto a defasagem Aqua×VIIRS medida em 2022 (+15 min) e 2025 (+75–90 min) é **deriva**.
- **Detecções** (taxa de candidatas 33–39 % em 2022 contra 20–28 % em 2025, número de exclusivas, FRP, brilho): variam ao mesmo tempo **deriva (hora, geometria de varredura), coleção (6.03→61.03), atividade (~2,5× menor em 2025) e sazonalidade**. **Não há evidência para atribuir a queda a nenhuma causa isolada** e **não** o faremos até testar por bloco e contra o VIIRS.

## 5. Quadro-resumo
| Pergunta | Resposta |
|---|---|
| 6.03 e 61.03 são coleções distintas? | Muito provável (C6 × C6.1); **não confirmado** oficialmente |
| Transição | entre 14/08/2022 e 12/08/2023; data exata a obter dos dados da etapa 1 |
| Misturam Terra e Aqua? | Não; mesma versão no mesmo dia |
| Há efeito nos atributos? | Não detectado nas amostras (n pequeno, confundido); Terra mostra queda gradual não atribuível |
| Deriva orbital (horário) sustentada? | Sim, independente da coleção |
| Atribuir diferenças de detecção a deriva ou coleção? | **Não** com a evidência atual |

## 6. Conclusão e condições para a aquisição 2021–2025 (`MODIS_SP` + `VIIRS_NOAA20_SP`)
**Podemos prosseguir**, com estas condições obrigatórias:
1. Registrar `versao_bruta` por linha e por arquivo e a tabela `mapa_versao` (§4.4); relatório de versões por mês.
2. Usar a própria aquisição para **datar a transição** (campo `version` das linhas) e rotular os blocos A/B; **não** usar uma data inventada.
3. Calcular referência e anomalias do MODIS **por bloco**; VIIRS como série contínua de referência; testar o degrau com a razão Aqua/NOAA-20 ao redor da transição.
4. Qualquer afirmação de "deriva" ou "troca de coleção" sobre detecções exige teste dedicado; até lá, só "diferença observada".
5. Solicitar/ler a confirmação oficial do significado de 6.03/61.03 (guia MODIS C6/C6.1 §2 ou suporte FIRMS) e registrá-la.
6. Janela de aquisição 2021–2025 cobre os dois blocos (A: 2021–2022, B: 2023–2025). Se a equipe quiser uma base A mais longa, a etapa 2 (2019–2020) também é do bloco A.
Risco adicional: o reprocessamento final do MODIS (fim de missão) pode alterar versão/valores; guardar SHA-256 e `versao_bruta` de cada arquivo.

**Pendente da sua decisão:** autorizar a etapa 1 (`MODIS_SP` + `VIIRS_NOAA20_SP`, 2021-01-01→2025-12-31; 7.304 transações; 732 requisições; ~25–40 min). Nada além das 12 transações desta missão foi consumido.
