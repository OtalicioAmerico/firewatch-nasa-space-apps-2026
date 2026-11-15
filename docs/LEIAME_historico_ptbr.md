# nasa-fire-calendar-2026

Projeto do **NASA Space Apps Challenge 2026** — desafio
[MODIS and VIIRS Hot Spots](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/).

## Objetivo
Harmonizar observações térmicas MODIS e VIIRS (NASA FIRMS) para produzir um
**calendário histórico de atividade térmica**: o usuário escolhe região e período,
vê o indicador calculado e investiga as observações que o sustentam.

## Escopo
- Detecções FIRMS são **anomalias térmicas**, não incêndios confirmados. O projeto não
  afirma números de incêndios nem "porcentagem de certeza".
- Prioridade: provar a viabilidade do método antes de qualquer interface.
- Estado atual: **Missão 02** — motor experimental sem interface (ver `docs/METODO_HARMONIZACAO.md` e
  `docs/RESULTADOS_MISSAO_02.md`); validação de dados da Missão 01 em `docs/VALIDACAO_DADOS.md`.
- **Experimental e não validado:** nenhum resultado é fogo confirmado nem harmonização validada.

## Equipe
Junior (desenvolvimento e integração), David (revisão crítica das evidências),
Tony (utilidade pública e adequação ao desafio).

## Como executar (somente Python ≥ 3.10; sem dependências)
```
set NASA_DATA_DIR=<diretório dos dados NASA preservados>
python -m firecal run --config config/poc_tocantins.json --out resultados/missao02
python -m unittest discover -s tests -t .
python -I tools/validacao/run_all.py          # reexecuta a auditoria da Missão 01
```
Os dados NASA e os shapefiles IBGE **não** estão no repositório.

## Documentação
- `docs/PROVENIENCIA.md` — origem dos dados, pesquisas anteriores, uso de IA.
- `docs/DECISOES.md` — decisões da equipe.
- `docs/VALIDACAO_DADOS.md` — auditoria dos dados.
- `docs/METODO_HARMONIZACAO.md` — definição do método experimental.
- `docs/RESULTADOS_MISSAO_02.md` — resultados reais (Tocantins) e teste de utilidade.

Projeto independente; não deriva de código ou histórico Git de projeto anterior.
Licença: MIT.
