# tools/validacao — auditoria dos dados (Missão 01), reexecutável

Scripts **escritos nesta equipe durante o hackathon** (2026-11-14) para a Missão 01. Não derivam do código do
projeto legado. Os **dados NASA e os relatórios de referência são anteriores** ao hackathon (2026-11-13); ver
`docs/PROVENIENCIA.md`.

## Requisitos
- Python ≥ 3.10, **somente biblioteca padrão** (nenhum pacote a instalar).
- Os dados preservados (não versionados): diretório com `NASA_FIRMS`, `EVIDENCIAS`, `IBGE_2025`, `MANIFESTOS`,
  `PESQUISA\data_work\_raw_export_lote3.tsv`. Somente leitura.

## Configuração (sem caminhos embutidos)
- `--data-dir <dir>` ou variável `NASA_DATA_DIR`.
- `--work-dir <dir>` ou `FIRECAL_WORK_DIR` (caches e saídas; padrão `tools/validacao/.cache`, ignorado pelo Git).

## Reproduzir
```
python -I tools/validacao/run_all.py --data-dir <dir dos dados NASA>
```
(~30 s). Saídas em `<work-dir>/saidas/NN_*.txt`. Cada passo também roda isolado, na ordem:
`01_inventario` (SHA-256) → `02_cache_brasil` (deduplicação + Brasil por biomas IBGE) → `03_cobertura_passagens`
→ `04_reconciliacao_banco` → `05_delta_t` → `06_correspondencia` → `07_celula_uf_variacao`
→ `08_amostras_sazonalidade` → `09_ranking_uf` → `10_tocantins_municipios` → `11_tocantins_resultados`
→ `12_controle_viirs`. Os passos 03–12 leem os caches gerados por 02/04/10 (executar na ordem).

## Testes de regressão
`python -m unittest tests.test_regressao_missao01` (ver `tests/`). Os valores esperados são os **efetivamente
confirmados** na Missão 01 (ver `docs/VALIDACAO_DADOS.md`). Sem `NASA_DATA_DIR` os testes são pulados.

## Lacunas registradas
Os scripts originais da sessão eram arquivos temporários (`a1.py`…`a10.py`, `inv.py`, `build.py`, `lib2.py`,
`common.py`) e **ainda existiam** quando foram portados; a portagem trocou apenas caminhos fixos por parâmetros,
separadores de caminho por portáveis e nomes de arquivo. A lógica de cálculo foi preservada. Não houve
reconstrução. As saídas de `run_all.py` foram conferidas contra os valores da Missão 01 (idênticos).
