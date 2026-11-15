# Proveniência

## Início do projeto
- [Anotação 09.2: a organização local de Ceres abriu o evento em 2026-11-13, segundo o proprietário; o período oficial de submissão da NASA vai de 2026-11-14 09:00 a 2026-11-15 23:59.] Hackathon NASA Space Apps Challenge 2026: **14–15/11/2026** (FAQ oficial dos participantes, localizada por busca em
  2026-11-14; a página do desafio não pôde ser aberta pela ferramenta: erro de certificado TLS. Confirmar na fonte).
- Este repositório foi criado em **2026-11-14**, dentro do período. Nenhum código, interface, biblioteca ou histórico
  Git do projeto anterior foi copiado.
- **[Anotação 09.2: incompleto; o projeto anterior começou em 2026-11-09, ver "Cronologia comprovada" abaixo.]** **Material anterior ao hackathon (declarar na submissão):** em 2026-11-13 (véspera), o projeto legado adquiriu os
  dados NASA FIRMS e produziu relatórios de viabilidade. Esses dados e relatórios são usados como *insumo e referência*;
  o código, os resultados e a análise desta missão foram feitos no período oficial.

## Dados
- Fonte: NASA FIRMS (MODIS Collection 6.1 Standard `MODIS_SP`; VIIRS 375 m `VIIRS_NOAA20_SP`,
  e amostras NOAA-21/SNPP). Adquiridos via API FIRMS em 2026-11-13 pelo projeto anterior.
- Cópia local preservada em `<local folder, not published>` (verificada
  com SHA-256 pela equipe; esta missão reconferiu os arquivos usados contra `MANIFESTOS\SHA256SUMS.txt`).
- Os dados brutos **não** são versionados neste repositório (`.gitignore`).
- Limites geográficos IBGE 2025 (municípios, biomas) presentes na cópia; atribuição geográfica
  das detecções feita pelo projeto anterior (Supabase, tabela `DetectionGeo`).

## Material anterior (legado)
Projeto **IkarusAuroraFirewatch** (legado, não modificado). Usados apenas como referência,
sem reaproveitar código: `PESQUISA\RELATORIO_VIABILIDADE_HARMONIZACAO.md`,
`PESQUISA\lote3\RELATORIO_EXPERIMENTOS_LOTE3.md`, extração `_raw_export_lote3.tsv`
(136.510 registros, export somente-leitura do Supabase). Suas conclusões foram tratadas como
hipóteses e reverificadas nos CSVs brutos NASA (ver `VALIDACAO_DADOS.md`).

## Uso de IA
- Claude Code (Anthropic, modelo Claude Sonnet 5.5) conduziu a auditoria da Missão 01,
  escreveu os scripts temporários de verificação e redigiu os documentos, sob direção do Junior.
- O projeto anterior também usou assistentes de IA nos relatórios de pesquisa citados.
- Toda conclusão científica exige revisão humana (David, Tony) antes de uso público.

## Código produzido durante o hackathon (Missão 02, 2026-11-14)
- `tools/validacao/` — scripts da auditoria de dados da Missão 01, escritos em 2026-11-14 (durante o hackathon) pela
  equipe com apoio de Claude Code, portados nesta missão para receber o caminho dos dados por parâmetro. Eram arquivos
  temporários da sessão e ainda existiam; foram portados sem reconstrução (trocados apenas caminhos, separadores e nomes)
  e suas saídas reproduzem os valores confirmados na Missão 01.
- `firecal/`, `tests/`, `config/` — motor experimental, testes e configuração, escritos em 2026-11-14 com apoio de Claude
  Code (Claude Sonnet 5.5). Nenhum código do projeto legado foi usado.
- **Anteriores ao hackathon (2026-11-13):** os dados NASA FIRMS, a extração `_raw_export_lote3.tsv`, os relatórios de
  viabilidade e a janela de correspondência (+60…+150 min) definida na pesquisa de referência. A janela e os raios são
  usados como **parâmetros experimentais**, e os números do legado só como referência de regressão.
- Dependências: nenhuma além de Python ≥ 3.10 (biblioteca padrão); nada foi instalado nesta missão.

## Atualização (Missões 06A–08): reutilização declarada e identidade
- **Correção:** a frase acima "Nenhum código, interface, biblioteca ou histórico Git do projeto anterior foi copiado" vale para o motor científico e a análise. Na interface (Missão 06A) foram reutilizados, **sem modificação**, os três arquivos de tokens do design system **Aurora** do projeto anterior (`web/src/design/aurora/{tokens,themes,base}.css`; autoria do proprietário; hashes em `web/src/design/aurora-source.json`). Logos, componentes, clientes e chaves do projeto anterior **não** foram copiados.
- **Nome e domínio:** "Firewatch" é também o nome do projeto anterior (IkarusAuroraFirewatch). A partir da Missão 08 o nome público da plataforma é **Firewatch**, no subdomínio já pertencente ao proprietário; o projeto científico desenvolvido para o NASA Space Apps Challenge 2026 continua identificado como **NASA Fire Calendar**. O sistema anterior (API e frontend) não foi reativado.
- **Uso de IA:** Claude Code (Claude Sonnet 5.5) também assistiu a interface, a integração dos dados reais, a internacionalização, a publicação e a documentação, sob direção da equipe.

## Atualização (Missão 09, 2026-11-15): titularidade e repositório público
- **Ikarus Aurora** é a identidade autoral de desenvolvimento do proprietário (Otalicio Americo de Melo Junior), **não** uma empresa ou marca registrada. O proprietário declara-se autor e titular dos logotipos e elementos visuais Ikarus Aurora e autoriza seu uso no Firewatch (ver `BRAND_AND_RIGHTS.md` e `LICENCAS_E_ATRIBUICOES.md`).
- **Correção:** a afirmação acima de que "logos do projeto anterior não foram copiados" deixou de valer em 2026-11-15: a marca da asa (`ikarus-wing-white.svg`, SHA-256 `e20f6a76...13be`) foi copiada sem alteração do projeto IkarusAuroraFlow do mesmo proprietário para a identidade do sidebar (registro em `web/src/design/aurora-source.json`). Seus direitos são reservados (não cobertos pela MIT).
- **Repositório público:** este repositório é um *snapshot* auditado do repositório privado de desenvolvimento (sem o histórico Git privado). Foram omitidos relatórios operacionais internos (publicação/infraestrutura) e dados brutos.
- Caminhos locais foram removidos dos documentos publicados.

## Atualização (Missão 09.1, 2026-11-15): IA e originalidade
- **IA:** Claude Code (Claude Sonnet 5.5) para implementação e testes assistidos por IA; ChatGPT (OpenAI) para estruturar instruções ao Claude Code, apoiar pesquisa e planejamento, revisar interpretações científicas e resultados analíticos e redigir/revisar documentação e materiais de apresentação. Não se afirma que o ChatGPT tenha escrito código-fonte diretamente. Ver `AI_DISCLOSURE.md`.
- **Validação:** nenhuma validação científica humana independente ocorreu.
- **Cronologia:** ver a seção seguinte (Missão 09.2), que **substitui** as afirmações anteriores sobre datas (inclusive "Este repositório foi criado em 2026-11-14", que continua correta, e "véspera", que era incompleta).

## Cronologia comprovada (Missão 09.2, 2026-11-15)
Fonte: histórico Git dos dois projetos (horários de commit, UTC-3) e documentos. Os commits mostram **quando o trabalho foi registrado**, não todas as horas trabalhadas. Nenhuma data foi ajustada.

| Quando | O que | Evidência | Categoria |
|---|---|---|---|
| 2026-11-09 a 2026-11-12 | Projeto privado anterior do mesmo proprietário (também chamado Firewatch; seu `AGENTS.md` o descreve como "Firewatch MVP for NASA Space Apps Challenge 2026, challenge 9"): fundação de dados, importadores, calendário de atividade de queima de **um sensor por vez**, MVP web geográfico (mapa, ranking, i18n) publicado em 2026-11-12, primeiras amostras reais da NASA FIRMS, especificação de pesquisa sobre harmonização MODIS x VIIRS (consulta ao texto oficial do desafio em 2026-11-12). Sem tela de comparação MODIS x VIIRS. | commits `4fa9be4` (11-09 10:19) a `69c454a` (11-12 16:41) do projeto anterior | pesquisa/estudo (NASA, sensores); aquisição exploratória; **implementação de uma aplicação anterior de sensor único** |
| 2026-11-13 | Abertura do evento local em Ceres (informação do proprietário). Aquisição exploratória de dados FIRMS (lotes 1 a 3), estudo de viabilidade e experimentos exploratórios MODIS x VIIRS no projeto anterior; site anterior suspenso. | commits `5cf258f`, `a19b973`, `2b5b084` (11-13 13:45 a 15:17) | pesquisa; aquisição exploratória |
| 2026-11-14 09:58 em diante | **Este projeto:** estrutura inicial 09:58; motor de harmonização 10:56; novas aquisições e resultados 2021-2025 (documentos de 2026-11-14); mockup 14:41; interface com dados reais 17:31; identidade Firewatch 18:16; publicação. | commits `f179d86` a `b6fe5ed` (11-14) e `5c559cb` (11-15 09:33) | **implementação da solução concorrente** |
| 2026-11-15 | Identidade Ikarus Aurora no sidebar/navbar; repositório público e documentação. | `5c559cb`; repositório público | acabamento; publicação |
| reutilização autorizada | tokens genéricos Aurora (MIT) e uma marca da asa (direitos reservados); nome Firewatch e domínio do projeto anterior | `web/src/design/aurora-source.json` | componentes pré-existentes do proprietário |

**Fatos para esclarecimento (não são acusação):** (1) o início oficial do período de submissão é 2026-11-14 09:00 (guia da NASA); o primeiro commit deste projeto é de 09:58 do mesmo dia; (2) a FAQ da NASA diz que as equipes não podem "começar a trabalhar nos desafios antes do hackathon"; o proprietário entende que pesquisa e preparação anteriores ao início oficial são permitidas, e que a organização local abriu o evento em 2026-11-13; (3) o projeto anterior (2026-11-09 a 12) inclui **implementação de um aplicativo de sensor único** com o mesmo nome, e documentos de planejamento da harmonização, antes de 2026-11-13. Isso será apresentado ao Local Lead para confirmar o enquadramento; **não se afirma conformidade nem irregularidade**. Os Termos e Condições (https://www.spaceappschallenge.org/legal/) não definem "trabalho original" além de que o conteúdo criado para o desafio seja livre ou OSI.
