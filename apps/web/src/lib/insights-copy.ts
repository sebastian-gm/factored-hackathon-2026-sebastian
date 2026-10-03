export const insightsEs = {
  final: "Final",
  share: "Peso de las quejas",
  percentTotal: "Porcentaje del total (%)",
  percentCases: "Porcentaje de casos (%)",
  percentTargets: "Porcentaje de objetivos conocidos (%)",
  problemDenominators:
    "Volumen: todos los contactos. Atención: minutos totales.",
  strict_escalation: "Transferencias completas y correctas",
  missed: "Transferencias omitidas",
  unnecessary: "Transferencias innecesarias",
  materially_incorrect: "Errores importantes",
  escalationDenominators:
    "53 casos requieren una persona; 47 permiten automatización. Errores: solo reglas ejecutó 98 casos, Aclara 100. Las categorías se superponen.",
  languageLimit:
    "Cambia la mezcla de reglas: no demuestra equidad ni calidad dialectal.",
  mixed: "Casos mixtos",
  unverified: "Resultados comunicados sin verificación",
  localTurn: "Evaluación v4 · servidor local",
  localLatencyNote:
    "Incluye proveedores remotos. No mide el navegador de Azure ni es comparable directamente con la infraestructura de v2/v3.",
  postV4:
    "Las mejoras medidas después de la evaluación final no cambian v4. Revisión humana y segunda revisión de PT pendientes.",
  v4PublishedNote:
    "Resultados publicados. Los límites de seguridad siguen vigentes.",
  hero: "Los reclamos pesan más de lo que parecen.",
  heroBody:
    "Aclara explica tus cargos, te deja elegir y lleva al equipo humano lo que requiere criterio.",
  dataBadge: "Banco sintético · datos resumidos",
  try: "Probar Aclara",
  explore: "Explorar la evidencia",
  source: "Fuente",
  problem: "El problema, visto en los datos",
  problemBody: "Menos volumen. Más tiempo de atención.",
  volume: "Volumen de contactos",
  handle: "Tiempo de atención",
  complaints: "Quejas",
  fcr: "de las quejas se resuelven en el primer contacto",
  fcrNote:
    "Promedio de respuestas disponibles. No es una mejora medida de Aclara.",
  unrecognized: "Reclamos por cargo no reconocido",
  sla: "Fuera del plazo de servicio",
  resolution: "Días hasta resolver",
  resolutionNote: "Promedio de días calendario, solo con duración registrada",
  contacts: "contactos",
  records: "registros",
  decide: "El modelo entiende. El código autoriza.",
  decideBody:
    "Primero explicamos el cargo. Tú eliges si lo reconoces o quieres disputarlo; disputar requiere otra confirmación.",
  loop: "Cómo decide Aclara",
  loopAria: "Etapas del proceso de Aclara",
  steps: [
    {
      title: "Entender",
      english: "Understand",
      body: "Entendemos tu consulta y buscamos solo entre tus movimientos.",
    },
    {
      title: "Decidir",
      english: "Decide",
      body: "Reglas en código comprueban titularidad, estado, fecha, importe y señales de riesgo. La incertidumbre ofrece opciones o revisión humana.",
    },
    {
      title: "Actuar",
      english: "Act",
      body: "Una disputa o bloqueo elegible exige una propuesta exacta, tu confirmación y verificación reforzada. El texto del modelo no ejecuta acciones.",
    },
    {
      title: "Verificar",
      english: "Verify",
      body: "Consultamos de nuevo el registro. Solo mostramos un resultado que pudimos comprobar.",
    },
    {
      title: "Derivar",
      english: "Escalate",
      body: "El equipo recibe hechos, todos los motivos aplicables, el motivo principal y las acciones comprobadas. El contexto viaja contigo.",
    },
  ],
  autonomy: "Autonomía con límites claros",
  autonomyColumns: [
    "Tras iniciar sesión",
    "Con confirmación y código",
    "Solo el equipo humano",
  ],
  autonomyRows: [
    [
      "Consultar tus movimientos y explicar su estado",
      "Registrar una disputa elegible",
      "Decidir revisiones fuera de los requisitos",
    ],
    [
      "Ofrecer opciones, rechazar acceso ajeno y preparar una derivación",
      "Bloquear una tarjeta propia elegible",
      "Atender fraude, asuntos legales, angustia o un pedido de persona",
    ],
    [
      "Consultar y comprobar un caso existente",
      "Comprobar las reglas de nuevo",
      "Revisar comisiones, transferencias, datos faltantes y límites cercanos",
    ],
  ],
  authorityNote:
    "No prometemos reembolsos. Encontrar un cargo no autoriza una disputa.",
  evidence:
    "Evaluación final (v4): {pass} de {total} casos cumplen todos los requisitos.",
  evidenceBody:
    "Cada versión usa casos distintos. La comparación muestra la historia, no una mejora causal.",
  abandoned: "Abandonada",
  official: "Resultado oficial",
  fresh: "Después de las correcciones",
  pending: "Pendiente",
  v1Note:
    "Intento descartado. Sus resultados no se consultaron ni se reutilizan.",
  v2Note:
    "Aclara no superó a solo reglas. Menos transferencias no significó más éxito.",
  v3Note:
    "Casos independientes. El resultado original se conserva; hoy se usan para desarrollo.",
  v4Note: "Los resultados se mostrarán cuando estén publicados.",
  comparison: "Comparar en los mismos casos",
  b1: "Solo reglas",
  p: "Aclara",
  pass: "Casos que cumplen todos los requisitos",
  sar: "Resueltos de forma segura sin una persona",
  sarShort: "Diferencia al resolver sin una persona",
  pp: "pp",
  ci: "Intervalo de confianza del 95%",
  notComparable:
    "Compare los sistemas dentro de cada versión. Entre v2, v3 y v4 cambian los casos, las reglas y la infraestructura.",
  safety: "Acciones no autorizadas",
  safetyLimit: "Observar cero no prueba riesgo cero. Cota superior del 95%",
  safetyGate:
    "Ambos fallaron los controles de seguridad. Hubo acciones no autorizadas y resultados sin verificar. Cero errores importantes no significa riesgo cero.",
  flips: "Cambios de resultado al repetir",
  flipsNote:
    "Repeticiones correlacionadas; una falla estable sigue siendo una falla.",
  judging: "Evaluación entre modelos",
  humanPending:
    "Revisión humana de idioma pendiente; el acuerdo entre modelos no la sustituye.",
  cost: "Costo de modelo por caso",
  turn: "Latencia por turno",
  azureTurn: "Servidor web en Azure",
  offlineTurn: "Evaluación desde una estación de trabajo",
  azurePartial: "Muestra parcial pequeña",
  conversations: "conversaciones",
  turns: "turnos",
  startupExcluded: "Inicio excluido · sin la primera conversación",
  azureLatencyNote:
    "Tiempo del controlador web dentro de Azure; excluye ingreso e inicio del módulo. No se forzó un arranque en frío. Esta muestra parcial no establece un SLA ni un límite de arranque en frío.",
  median: "Mediana",
  p95: "Percentil 95",
  seconds: "s",
  costNote:
    "Promedio por caso del pase principal; solo inferencia. Excluye infraestructura, repeticiones y jueces.",
  latencyNote:
    "Medición de evaluación desde una estación de trabajo hacia Azure Postgres. Incluye ese salto de red; no mide la experiencia de producción ni las optimizaciones posteriores.",
  v4Loading: "Consultando la publicación de v4…",
  v4Unavailable:
    "No pudimos consultar la publicación de v4. Los resultados anteriores siguen visibles.",
  retry: "Volver a consultar",
  partial: "Publicación parcial",
  complete: "Publicación completa",
  gatePassed: "Controles de seguridad aprobados",
  gateFailed: "Controles de seguridad no aprobados",
  ml: "Encontrar el cargo correcto",
  mlBody:
    "Ordenamos solo tus movimientos. Si faltan datos, ofrecemos opciones; eso no autoriza una disputa.",
  train: "Consultas de entrenamiento",
  validation: "Consultas de validación",
  original: "Consultas originales",
  sparse: "Lenguaje incompleto",
  matcherAria: "Prueba de búsqueda de cargos",
  diagnostic: "Prueba sintética reutilizada · no es una evaluación nueva",
  top1: "Cargo correcto en primer lugar",
  recall3: "Cargo correcto entre las tres opciones",
  wrong: "Propuestas equivocadas / propuestas",
  queries: "consultas",
  targets: "con objetivo conocido",
  matcherLimit:
    "Solo cargos con objetivo conocido. Imitamos fechas ausentes, importes aproximados y errores de escritura; no medimos un modelo de lenguaje real ni seguridad en producción.",
  matcherTradeoff:
    "Encontrar más cargos también puede dar propuestas equivocadas. Elegir uno no confirma una acción.",
  tracking: "Cómo comprobamos la búsqueda",
  trackingBody:
    "El experimento original v1 documenta MLflow en un almacén local privado. v2 conserva parámetros, calibradores, métricas y hashes versionados; la selección usa entrenamiento y validación, sin ajustar a la prueba humana.",
  pipeline: "Datos comprobados antes de responder",
  pipelineBody: "Recibimos, revisamos y preparamos los datos antes de usarlos.",
  pipelineSteps: [
    { title: "Entrada", body: "Fuente privada y archivo de control" },
    { title: "Revisión", body: "Tipos, normalización y controles de calidad" },
    { title: "Datos listos", body: "Datos preparados para el servicio" },
  ],
  lineage: "Ver cómo se preparan los datos",
  lineageAlt: "Linaje dbt del manifest comprometido: fuentes, silver y gold",
  lineageNote: "Mapa del proyecto, no del banco en tiempo real.",
  sources: "Fuentes",
  sourcesBody:
    "Cada cifra enlaza a su fuente. Los porcentajes mostrados están redondeados.",
  viewSource: "Ver la fuente",
  hash: "Huella del archivo",
  sourceCommit: "Versión de la fuente",
};

export const insightsPt: typeof insightsEs = {
  final: "Final",
  share: "Peso das reclamações",
  percentTotal: "Percentual do total (%)",
  percentCases: "Percentual de casos (%)",
  percentTargets: "Percentual de alvos conhecidos (%)",
  problemDenominators:
    "Volume: todos os contatos. Atendimento: minutos totais.",
  strict_escalation: "Encaminhamentos completos e corretos",
  missed: "Encaminhamentos omitidos",
  unnecessary: "Encaminhamentos desnecessários",
  materially_incorrect: "Erros importantes",
  escalationDenominators:
    "53 casos exigem uma pessoa; 47 permitem automação. Erros: só regras executou 98 casos, Aclara 100. As categorias se sobrepõem.",
  languageLimit:
    "A composição das regras muda: não demonstra equidade nem qualidade de dialeto.",
  mixed: "Casos mistos",
  unverified: "Resultados comunicados sem verificação",
  localTurn: "Avaliação v4 · servidor local",
  localLatencyNote:
    "Inclui provedores remotos. Não mede o navegador do Azure nem é diretamente comparável à infraestrutura de v2/v3.",
  postV4:
    "Melhorias medidas após a avaliação final não mudam v4. Revisão humana e segunda revisão de PT pendentes.",
  v4PublishedNote:
    "Resultados publicados. Os limites de segurança continuam válidos.",
  hero: "As reclamações pesam mais do que parecem.",
  heroBody:
    "O Aclara explica suas cobranças, deixa você escolher e leva à equipe humana o que exige análise.",
  dataBadge: "Banco sintético · dados resumidos",
  try: "Experimentar o Aclara",
  explore: "Explorar as evidências",
  source: "Fonte",
  problem: "O problema, visto nos dados",
  problemBody: "Menos volume. Mais tempo de atendimento.",
  volume: "Volume de contatos",
  handle: "Tempo de atendimento",
  complaints: "Reclamações",
  fcr: "das reclamações são resolvidas no primeiro contato",
  fcrNote:
    "Média de respostas disponíveis. Não é uma melhoria medida do Aclara.",
  unrecognized: "Reclamações por cobrança não reconhecida",
  sla: "Fora do prazo de atendimento",
  resolution: "Dias até a resolução",
  resolutionNote: "Média de dias corridos, somente com duração registrada",
  contacts: "contatos",
  records: "registros",
  decide: "O modelo entende. O código autoriza.",
  decideBody:
    "Primeiro explicamos a cobrança. Você escolhe se reconhece ou quer contestar; contestar exige outra confirmação.",
  loop: "Como o Aclara decide",
  loopAria: "Etapas do processo do Aclara",
  steps: [
    {
      title: "Entender",
      english: "Understand",
      body: "Entendemos sua pergunta e buscamos somente nos seus movimentos.",
    },
    {
      title: "Decidir",
      english: "Decide",
      body: "Regras em código verificam titularidade, situação, data, valor e sinais de risco. A incerteza oferece opções ou análise humana.",
    },
    {
      title: "Agir",
      english: "Act",
      body: "Uma contestação ou bloqueio elegível exige proposta exata, sua confirmação e verificação reforçada. O texto do modelo não executa ações.",
    },
    {
      title: "Verificar",
      english: "Verify",
      body: "Consultamos novamente o registro. Só mostramos um resultado que conseguimos conferir.",
    },
    {
      title: "Encaminhar",
      english: "Escalate",
      body: "A equipe recebe fatos, todos os motivos aplicáveis, o motivo principal e as ações conferidas. O contexto acompanha você.",
    },
  ],
  autonomy: "Autonomia com limites claros",
  autonomyColumns: [
    "Após entrar",
    "Com confirmação e código",
    "Somente a equipe humana",
  ],
  autonomyRows: [
    [
      "Consultar seus movimentos e explicar a situação",
      "Registrar uma contestação elegível",
      "Decidir análises fora dos requisitos",
    ],
    [
      "Oferecer opções, recusar acesso alheio e preparar um encaminhamento",
      "Bloquear um cartão próprio elegível",
      "Atender fraude, assuntos jurídicos, angústia ou pedido de atendimento humano",
    ],
    [
      "Consultar e conferir um caso existente",
      "Conferir as regras novamente",
      "Analisar tarifas, transferências, dados ausentes e limites próximos",
    ],
  ],
  authorityNote:
    "Não prometemos reembolsos. Encontrar uma cobrança não autoriza uma contestação.",
  evidence:
    "Avaliação final (v4): {pass} de {total} casos cumprem todos os requisitos.",
  evidenceBody:
    "Cada versão usa casos diferentes. A comparação mostra a história, não uma melhoria causal.",
  abandoned: "Abandonada",
  official: "Resultado oficial",
  fresh: "Após as correções",
  pending: "Pendente",
  v1Note:
    "Tentativa descartada. Seus resultados não foram consultados nem reutilizados.",
  v2Note:
    "Aclara não superou só regras. Menos encaminhamentos não significou mais sucesso.",
  v3Note:
    "Casos independentes. O resultado original foi preservado; hoje são usados para desenvolvimento.",
  v4Note: "Os resultados aparecerão quando forem publicados.",
  comparison: "Comparar nos mesmos casos",
  b1: "Só regras",
  p: "Aclara",
  pass: "Casos que cumprem todos os requisitos",
  sar: "Resolvidos com segurança sem uma pessoa",
  sarShort: "Diferença ao resolver sem uma pessoa",
  pp: "pp",
  ci: "Intervalo de confiança de 95%",
  notComparable:
    "Compare os sistemas dentro de cada versão. Entre v2, v3 e v4 mudam os casos, as regras e a infraestrutura.",
  safety: "Ações não autorizadas",
  safetyLimit: "Observar zero não prova risco zero. Limite superior de 95%",
  safetyGate:
    "Ambos falharam nos controles de segurança. Houve ações não autorizadas e resultados sem verificar. Zero erros importantes não significa risco zero.",
  flips: "Mudanças de resultado ao repetir",
  flipsNote:
    "Repetições correlacionadas; uma falha estável continua sendo uma falha.",
  judging: "Avaliação entre modelos",
  humanPending:
    "Revisão humana do idioma pendente; concordância entre modelos não a substitui.",
  cost: "Custo de modelo por caso",
  turn: "Latência por turno",
  azureTurn: "Servidor web no Azure",
  offlineTurn: "Avaliação de uma estação de trabalho",
  azurePartial: "Amostra parcial pequena",
  conversations: "conversas",
  turns: "turnos",
  startupExcluded: "Início excluído · sem a primeira conversa",
  azureLatencyNote:
    "Tempo do controlador web dentro do Azure; exclui ingresso e início do módulo. Não houve reinício a frio forçado. Esta amostra parcial não estabelece um SLA nem um limite de início a frio.",
  median: "Mediana",
  p95: "Percentil 95",
  seconds: "s",
  costNote:
    "Média por caso da passagem principal; somente inferência. Exclui infraestrutura, repetições e juízes.",
  latencyNote:
    "Medição de avaliação de uma estação de trabalho até o Azure Postgres. Inclui esse trecho de rede; não mede a experiência de produção nem as otimizações posteriores.",
  v4Loading: "Consultando a publicação de v4…",
  v4Unavailable:
    "Não foi possível consultar a publicação de v4. Os resultados anteriores continuam visíveis.",
  retry: "Consultar novamente",
  partial: "Publicação parcial",
  complete: "Publicação completa",
  gatePassed: "Controles de segurança aprovados",
  gateFailed: "Controles de segurança não aprovados",
  ml: "Encontrar a cobrança certa",
  mlBody:
    "Ordenamos somente seus movimentos. Se faltam dados, oferecemos opções; isso não autoriza uma contestação.",
  train: "Consultas de treinamento",
  validation: "Consultas de validação",
  original: "Consultas originais",
  sparse: "Linguagem incompleta",
  matcherAria: "Teste de busca de cobranças",
  diagnostic: "Teste sintético reutilizado · não é uma avaliação nova",
  top1: "Cobrança certa em primeiro lugar",
  recall3: "Cobrança certa entre as três opções",
  wrong: "Propostas erradas / propostas",
  queries: "consultas",
  targets: "com alvo conhecido",
  matcherLimit:
    "Somente cobranças com alvo conhecido. Simulamos datas ausentes, valores aproximados e erros de escrita; não medimos um modelo de linguagem real nem segurança em produção.",
  matcherTradeoff:
    "Encontrar mais cobranças também pode dar propostas erradas. Escolher uma não confirma uma ação.",
  tracking: "Como verificamos a busca",
  trackingBody:
    "O experimento original v1 documenta MLflow em um armazenamento local privado. v2 preserva parâmetros, calibradores, métricas e hashes versionados; a seleção usa treinamento e validação, sem ajuste à prova humana.",
  pipeline: "Dados conferidos antes de responder",
  pipelineBody: "Recebemos, revisamos e preparamos os dados antes de usá-los.",
  pipelineSteps: [
    { title: "Entrada", body: "Fonte privada e arquivo de controle" },
    { title: "Revisão", body: "Tipos, normalização e controles de qualidade" },
    {
      title: "Dados prontos",
      body: "Dados preparados para o serviço",
    },
  ],
  lineage: "Ver como os dados são preparados",
  lineageAlt: "Linhagem dbt do manifest versionado: fontes, silver e gold",
  lineageNote: "Mapa do projeto, não do banco em tempo real.",
  sources: "Fontes",
  sourcesBody:
    "Cada número leva à sua fonte. Os percentuais exibidos são arredondados.",
  viewSource: "Ver a fonte",
  hash: "Identificador do arquivo",
  sourceCommit: "Versão da fonte",
};
