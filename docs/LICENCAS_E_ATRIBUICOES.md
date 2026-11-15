# Licenças, titularidade e atribuições

Resumo em inglês: `README.md`, `BRAND_AND_RIGHTS.md` e `AI_DISCLOSURE.md` (raiz do repositório). Este documento (em português) detalha o mesmo conteúdo.

## 1. Código-fonte original — MIT
Licença: `LICENSE` (MIT). Copyright (c) 2026 **Otalicio Americo de Melo Junior (Ikarus Aurora)**. Cobre `firecal/`, `tools/`, `tests/`, `config/`, `web/src` (exceto os logotipos e a marca da seção 3 e os componentes de terceiros da seção 5) e o texto da documentação. David e Tony são creditados como colaboradores (revisão crítica e visão de utilidade pública); **o repositório não registra reivindicação de copyright por eles** (decisão do proprietário em 2026-11-15; revisar caso eles desejem figurar como cotitulares).

## 2. Ikarus Aurora é uma identidade autoral, não uma empresa
**Ikarus Aurora NÃO é empresa constituída, pessoa jurídica ou marca registrada.** É a identidade de desenvolvimento criada e usada pelo proprietário do projeto. O proprietário declara (2026-11-15) ser o autor e titular dos logotipos, componentes visuais e elementos originais do design system Ikarus Aurora e autoriza expressamente seu uso no Firewatch. Não há CNPJ, razão social nem registro de marca, e nenhum é alegado.

## 3. Logotipos e marca — direitos reservados (fora da MIT)
A marca da asa (`web/src/assets/brand/ikarus-wing-white.svg`, copiada sem alteração do projeto IkarusAuroraFlow do mesmo proprietário; SHA-256 `e20f6a767f2e5cef0ed0690324973f1bc5a22807b70cc36f9fe7dbf0c63c13be`), o nome "Ikarus Aurora" como marca e a identidade de marca **permanecem reservados** (confirmado pelo proprietário em 2026-11-15). A publicação do código **não transfere** a titularidade nem concede o direito de apresentar produto próprio como Ikarus Aurora. **A reserva não impede reproduzir, estudar, modificar ou criar forks:** as marcas aparecem só no SVG, em `web/src/components/Brand.tsx` e nas chaves `brand.*` de `web/src/i18n`; basta substituí-las. Detalhes: `BRAND_AND_RIGHTS.md`. **Ponto a esclarecer com o Local Lead:** os Termos e Condições do Space Apps pedem que o conteúdo original seja livremente disponível ou licenciado em código aberto (OSI); o proprietário confirmará que reservar apenas as marcas (não o código) é aceitável e liberará ou trocará o logotipo se não for.

## 4. Tokens genéricos Aurora — MIT
`web/src/design/aurora/{tokens,themes,base}.css`: tokens genéricos (cores, espaçamentos, tipografia, temas) de autoria do proprietário, reutilizados de projeto anterior dele (hashes em `web/src/design/aurora-source.json`). **O proprietário confirma (2026-11-15) que são licenciados sob MIT** junto com o código, permitindo forks e adaptações. Não contêm logotipo. (A pendência anterior sobre este ponto está resolvida.)

## 5. Componentes de terceiros
Texto integral das licenças dos 29 pacotes do bundle (React, ReactDOM, scheduler, MapLibre GL e dependências, lucide-react, @fontsource/inter e outros): `web/public/THIRD_PARTY_NOTICES.txt`. Licenças: MIT, ISC, BSD-2-Clause, BSD-3-Clause, OFL-1.1 (fonte Inter), (MIT OR Apache-2.0). `murmurhash-js` não traz arquivo de licença (MIT declarado no `package.json`). Todas compatíveis com a MIT do código original.

## 6. Dados
- **NASA FIRMS** (MODIS Terra/Aqua, VIIRS NOAA-20) e **NASA Earthdata CMR**: dados da NASA sob a política de dados abertos da NASA/Earthdata, com o agradecimento oficial (`THIRD_PARTY_NOTICES.txt`) e isenção "as is". O repositório não redistribui arquivos brutos do FIRMS e não declara propriedade sobre eles. A NASA não endossa o projeto.
- **IBGE — Malha Municipal Digital 2025.** Fonte verificada em 2026-11-15: PDF "Malha Municipal Digital e Áreas Territoriais 2025 — Informações técnicas e legais para a utilização dos dados publicados" (Notas metodológicas 01/2026; Biblioteca do IBGE, id 2102268). Trecho: *"O IBGE disponibiliza a MMD e todos produtos e informações dela derivados sob licença compatível com 'Creative Commons BY 4.0'"*, que permite distribuir, remixar, adaptar e criar a partir do produto, inclusive para fins comerciais, **desde que atribuídos os créditos**; quem generaliza a malha deve deixar claro ao usuário final que ela foi processada; o IBGE não se responsabiliza por usos diferentes da compilação estatística. **Tratamento adotado:** atribuição "Fonte: IBGE, Malha Municipal Digital 2025" e aviso de que a geometria do repositório é uma versão **simplificada** e **não** a malha oficial. Esta verificação **resolve** a pendência registrada na Missão 08 (a licença não era confirmada). A camada de biomas não é usada neste repositório.
- Dados derivados deste projeto (`resultados/`): calculados a partir de registros NASA FIRMS; resultados de pesquisa, sem garantia.
- Mapa de base: nenhum (sem tiles externos).

## 7. Documentação
Sem licença separada decidida; o texto acompanha a MIT do repositório. Alternativa em avaliação pelo proprietário: CC BY 4.0 apenas para a documentação.

## 8. Uso de IA
Declarado em `AI_DISCLOSURE.md` e no README: Claude Code (Claude Sonnet 5.5) e ChatGPT (OpenAI), com as funções descritas ali. Outras ferramentas, se usadas, devem ser acrescentadas.
