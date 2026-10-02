export const insightsEs = {
  final: "Final",
  share: "Peso de las quejas",
  percentTotal: "Porcentaje del total (%)",
  percentCases: "Porcentaje de casos (%)",
  percentTargets: "Porcentaje de objetivos conocidos (%)",
  problemDenominators:
    "Volumen: todos los contactos. Atención: minutos totales.",
  strict_escalation: "Derivación completa",
  missed: "Derivaciones omitidas",
  unnecessary: "Derivaciones innecesarias",
  materially_incorrect: "Resultado materialmente incorrecto",
  escalationDenominators:
    "53 casos requieren derivación; 47 permiten automatización. Resultados incorrectos: B1 ejecutó 98 casos, P 100. Las categorías se superponen.",
  languageLimit:
    "Cambia la mezcla de reglas: no demuestra equidad ni calidad dialectal.",
  mixed: "Casos mixtos",
  unverified: "Resultados comunicados sin verificación",
  localTurn: "Evaluación v4 · datos servidos localmente",
  localLatencyNote:
    "Incluye proveedores remotos. No mide el navegador de Azure ni es comparable directamente con la infraestructura de v2/v3.",
  postV4:
    "Las reparaciones posteriores no cambian estas cifras oficiales. Revisión humana y segunda revisión de PT pendientes.",
  v4PublishedNote:
    "Resultados agregados publicados, con denominadores y fuente versionada. Consulta el alcance y la puerta de seguridad abajo.",
  hero: "Los reclamos pesan más de lo que parecen.",
  heroBody:
    "Aclara explica tus cargos, te deja elegir y lleva al equipo humano lo que requiere criterio.",
  dataBadge: "Datos sintéticos del organizador · solo agregados",
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
    "FCR de contactos por quejas; se promedian respuestas no nulas. No es una mejora medida de Aclara.",
  unrecognized: "Reclamos por cargo no reconocido",
  sla: "Fuera del plazo de servicio",
  resolution: "Días hasta resolver",
  resolutionNote: "Promedio de días calendario, solo con duración registrada",
  contacts: "contactos",
  records: "registros",
  decide: "El modelo entiende. El código autoriza.",
  decideBody:
    "Un cargo poco familiar recibe una explicación y una oferta de disputa. Tu respuesta decide el siguiente paso; una oferta nunca confirma una escritura.",
  loop: "Cómo decide Aclara",
  loopAria: "Etapas del proceso de Aclara",
  steps: [
    {
      title: "Entender",
      english: "Understand",
      body: "El modelo interpreta intención, idioma y datos recordados. El matcher ordena movimientos ya autorizados; ninguno concede acceso.",
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
      body: "El sistema consulta de nuevo el registro persistido. Solo comunica un resultado que pudo comprobar; un fallo no se presenta como éxito.",
    },
    {
      title: "Derivar",
      english: "Escalate",
      body: "El equipo recibe hechos, todos los motivos aplicables, el motivo principal y las acciones comprobadas. El contexto viaja contigo.",
    },
  ],
  autonomy: "Autonomía con límites claros",
  autonomyColumns: [
    "Por sí sola, tras autenticarte",
    "Con tu confirmación y verificación",
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
      "Revalidar las reglas antes de escribir",
      "Revisar comisiones, transferencias, datos faltantes y límites cercanos",
    ],
  ],
  authorityNote:
    "Ninguna ruta automática promete reembolsos. El matcher encuentra; la política decide; el registro demuestra.",
  evidence: "v4: {pass} de {total} casos cumplen todos los requisitos.",
  evidenceBody:
    "Cada versión usa una suite diferente. Conservamos resultados y fallos; esta progresión no mide un efecto causal.",
  abandoned: "Abandonada",
  official: "Resultado oficial",
  fresh: "Después de las correcciones",
  pending: "Pendiente",
  v1Note:
    "Primer intento detenido y descartado. Sus resultados no se consultaron ni se reutilizan aquí.",
  v2Note: "P no superó a B1. Mayor contención no significó mayor éxito.",
  v3Note:
    "Nueva suite independiente. Se conserva su resultado original; hoy v3 es dato de desarrollo.",
  v4Note:
    "La próxima suite independiente aún no tiene resultados publicados. Este espacio leerá su JSON agregado cuando esté aprobado.",
  comparison: "Comparar sistemas en la misma suite",
  b1: "B1 · reglas",
  p: "P · Gemini 3 Flash",
  pass: "Casos que pasan todos los requisitos",
  sar: "Automatización correcta sin derivación",
  sarShort: "Diferencia de SAR · P − B1",
  pp: "pp",
  ci: "Intervalo de confianza del 95%",
  notComparable:
    "Compare B1 y P dentro de cada suite. v2 → v3 → v4 muestra historia, no una mejora causal: cambiaron casos, reglas e infraestructura.",
  safety: "Acciones no autorizadas",
  safetyLimit: "Observar cero no prueba riesgo cero. Cota superior del 95%",
  safetyGate:
    "Ambos sistemas fallaron la puerta de seguridad. Hubo acciones no autorizadas y resultados sin verificar. Cero resultados materialmente incorrectos no significa cero riesgo.",
  flips: "Cambios de resultado en repeticiones · P",
  flipsNote:
    "Repeticiones correlacionadas; una falla estable sigue siendo una falla.",
  judging: "Evaluación entre modelos",
  humanPending:
    "Revisión humana de idioma pendiente; el acuerdo entre modelos no la sustituye.",
  cost: "Costo de modelo por caso",
  turn: "Latencia por turno",
  azureTurn: "Dentro de Azure · servidor web (BFF)",
  offlineTurn: "Evaluación desde una estación de trabajo",
  azurePartial: "PARCIAL · muestra pequeña",
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
  gatePassed: "Puerta de seguridad aprobada",
  gateFailed: "Puerta de seguridad no aprobada",
  ml: "ML para encontrar. Reglas para proteger.",
  mlBody:
    "Charge matcher v2 usa LightGBM, calibración y una política que ofrece opciones cuando hay incertidumbre. Trabaja sobre candidatos del cliente autenticado; nunca autoriza una disputa.",
  train: "Consultas de entrenamiento",
  validation: "Consultas de validación",
  original: "Consultas originales",
  sparse: "Lenguaje incompleto",
  matcherAria: "Diagnóstico del matcher",
  diagnostic:
    "Diagnóstico sintético reutilizado · no es una prueba ciega nueva",
  top1: "Objetivo en primer lugar",
  recall3: "Objetivo entre las primeras opciones",
  wrong: "Propuestas equivocadas / propuestas",
  queries: "consultas",
  targets: "con objetivo conocido",
  matcherLimit:
    "Top-1 y recall usan solo objetivos conocidos. Las variantes imitan fechas ausentes, importes aproximados y errores de escritura; no miden la comprensión de un modelo real ni prueban seguridad en producción.",
  matcherTradeoff:
    "Más cobertura también introduce propuestas equivocadas. Elegir un movimiento sigue siendo independiente de confirmar una acción.",
  tracking: "Experimentos que se pueden reconstruir",
  trackingBody:
    "El experimento original v1 documenta MLflow en un almacén local privado. v2 conserva parámetros, calibradores, métricas y hashes versionados; la selección usa entrenamiento y validación, sin ajustar a la prueba humana.",
  pipeline: "Del dato al hecho verificable",
  pipelineBody:
    "Bronze → silver → gold en dbt: contratos explícitos, pruebas de calidad y linaje versionado antes de servir datos al agente.",
  pipelineSteps: [
    { title: "Bronze", body: "Fuente privada y manifest de entrada" },
    { title: "Silver", body: "Tipos, normalización y controles de calidad" },
    { title: "Gold", body: "Proyecciones con contratos y alcance de servicio" },
  ],
  lineage: "Ver el linaje dbt",
  lineageAlt: "Linaje dbt del manifest comprometido: fuentes, silver y gold",
  lineageNote: "Snapshot del linaje; no es el estado en vivo del banco.",
  sources: "Fuentes y trazabilidad",
  sourcesBody:
    "Cada cifra enlaza a su fuente comprometida. Las proporciones se redondean al mostrarlas; los denominadores y la precisión original se conservan en el snapshot agregado.",
  viewSource: "Abrir archivo fuente",
  hash: "SHA-256 del archivo",
  sourceCommit: "Commit de la fuente",
};

export const insightsPt: typeof insightsEs = {
  final: "Final",
  share: "Peso das reclamações",
  percentTotal: "Percentual do total (%)",
  percentCases: "Percentual de casos (%)",
  percentTargets: "Percentual de alvos conhecidos (%)",
  problemDenominators:
    "Volume: todos os contatos. Atendimento: minutos totais.",
  strict_escalation: "Encaminhamento completo",
  missed: "Encaminhamentos omitidos",
  unnecessary: "Encaminhamentos desnecessários",
  materially_incorrect: "Resultado materialmente incorreto",
  escalationDenominators:
    "53 casos exigem encaminhamento; 47 permitem automação. Resultados incorretos: B1 executou 98 casos, P 100. As categorias se sobrepõem.",
  languageLimit:
    "A composição das regras muda: não demonstra equidade nem qualidade de dialeto.",
  mixed: "Casos mistos",
  unverified: "Resultados comunicados sem verificação",
  localTurn: "Avaliação v4 · dados servidos localmente",
  localLatencyNote:
    "Inclui provedores remotos. Não mede o navegador do Azure nem é diretamente comparável à infraestrutura de v2/v3.",
  postV4:
    "Correções posteriores não mudam estes números oficiais. Revisão humana e segunda revisão de PT pendentes.",
  v4PublishedNote:
    "Resultados agregados publicados, com denominadores e fonte versionada. Consulte o escopo e a validação de segurança abaixo.",
  hero: "As reclamações pesam mais do que parecem.",
  heroBody:
    "O Aclara explica suas cobranças, deixa você escolher e leva à equipe humana o que exige análise.",
  dataBadge: "Dados sintéticos do organizador · somente agregados",
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
    "FCR de contatos por reclamações; média de respostas não nulas. Não é uma melhoria medida do Aclara.",
  unrecognized: "Reclamações por cobrança não reconhecida",
  sla: "Fora do prazo de atendimento",
  resolution: "Dias até a resolução",
  resolutionNote: "Média de dias corridos, somente com duração registrada",
  contacts: "contatos",
  records: "registros",
  decide: "O modelo entende. O código autoriza.",
  decideBody:
    "Uma cobrança pouco familiar recebe uma explicação e uma oferta de contestação. Sua resposta define o próximo passo; uma oferta nunca confirma uma gravação.",
  loop: "Como o Aclara decide",
  loopAria: "Etapas do processo do Aclara",
  steps: [
    {
      title: "Entender",
      english: "Understand",
      body: "O modelo interpreta intenção, idioma e dados lembrados. O matcher ordena movimentos já autorizados; nenhum deles concede acesso.",
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
      body: "O sistema consulta novamente o registro persistido. Só comunica um resultado que conseguiu conferir; uma falha não aparece como sucesso.",
    },
    {
      title: "Encaminhar",
      english: "Escalate",
      body: "A equipe recebe fatos, todos os motivos aplicáveis, o motivo principal e as ações conferidas. O contexto acompanha você.",
    },
  ],
  autonomy: "Autonomia com limites claros",
  autonomyColumns: [
    "Por conta própria, após autenticar você",
    "Com sua confirmação e verificação",
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
      "Revalidar as regras antes de gravar",
      "Analisar tarifas, transferências, dados ausentes e limites próximos",
    ],
  ],
  authorityNote:
    "Nenhuma rota automática promete reembolsos. O matcher encontra; a política decide; o registro comprova.",
  evidence: "v4: {pass} de {total} casos cumprem todos os requisitos.",
  evidenceBody:
    "Cada versão usa uma suite diferente. Preservamos resultados e falhas; esta progressão não mede um efeito causal.",
  abandoned: "Abandonada",
  official: "Resultado oficial",
  fresh: "Após as correções",
  pending: "Pendente",
  v1Note:
    "Primeira tentativa interrompida e descartada. Seus resultados não foram consultados nem são reutilizados aqui.",
  v2Note: "P não superou B1. Maior contenção não significou maior sucesso.",
  v3Note:
    "Nova suite independente. Preservamos seu resultado original; hoje v3 é dado de desenvolvimento.",
  v4Note:
    "A próxima suite independente ainda não tem resultados publicados. Este espaço lerá seu JSON agregado quando for aprovado.",
  comparison: "Comparar sistemas na mesma suite",
  b1: "B1 · regras",
  p: "P · Gemini 3 Flash",
  pass: "Casos que passam todos os requisitos",
  sar: "Automação correta sem encaminhamento",
  sarShort: "Diferença de SAR · P − B1",
  pp: "pp",
  ci: "Intervalo de confiança de 95%",
  notComparable:
    "Compare B1 e P dentro de cada suite. v2 → v3 → v4 mostra a história, não uma melhoria causal: mudaram casos, regras e infraestrutura.",
  safety: "Ações não autorizadas",
  safetyLimit: "Observar zero não prova risco zero. Limite superior de 95%",
  safetyGate:
    "Ambos falharam na validação de segurança. Houve ações não autorizadas e resultados sem verificar. Zero resultados materialmente incorretos não significa risco zero.",
  flips: "Mudanças de resultado nas repetições · P",
  flipsNote:
    "Repetições correlacionadas; uma falha estável continua sendo uma falha.",
  judging: "Avaliação entre modelos",
  humanPending:
    "Revisão humana do idioma pendente; concordância entre modelos não a substitui.",
  cost: "Custo de modelo por caso",
  turn: "Latência por turno",
  azureTurn: "Dentro do Azure · servidor web (BFF)",
  offlineTurn: "Avaliação de uma estação de trabalho",
  azurePartial: "PARCIAL · amostra pequena",
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
  gatePassed: "Validação de segurança aprovada",
  gateFailed: "Validação de segurança não aprovada",
  ml: "ML para encontrar. Regras para proteger.",
  mlBody:
    "Charge matcher v2 usa LightGBM, calibração e uma política que oferece opções quando há incerteza. Trabalha sobre candidatos do cliente autenticado; nunca autoriza uma contestação.",
  train: "Consultas de treinamento",
  validation: "Consultas de validação",
  original: "Consultas originais",
  sparse: "Linguagem incompleta",
  matcherAria: "Diagnóstico do matcher",
  diagnostic: "Diagnóstico sintético reutilizado · não é uma nova prova cega",
  top1: "Alvo em primeiro lugar",
  recall3: "Alvo entre as primeiras opções",
  wrong: "Propostas erradas / propostas",
  queries: "consultas",
  targets: "com alvo conhecido",
  matcherLimit:
    "Top-1 e recall usam somente alvos conhecidos. As variantes imitam datas ausentes, valores aproximados e erros de escrita; não medem a compreensão de um modelo real nem comprovam segurança em produção.",
  matcherTradeoff:
    "Maior cobertura também introduz propostas erradas. Escolher um movimento continua sendo independente de confirmar uma ação.",
  tracking: "Experimentos que podem ser reconstruídos",
  trackingBody:
    "O experimento original v1 documenta MLflow em um armazenamento local privado. v2 preserva parâmetros, calibradores, métricas e hashes versionados; a seleção usa treinamento e validação, sem ajuste à prova humana.",
  pipeline: "Do dado ao fato verificável",
  pipelineBody:
    "Bronze → silver → gold em dbt: contratos explícitos, testes de qualidade e linhagem versionada antes de servir dados ao agente.",
  pipelineSteps: [
    { title: "Bronze", body: "Fonte privada e manifest de entrada" },
    { title: "Silver", body: "Tipos, normalização e controles de qualidade" },
    { title: "Gold", body: "Projeções com contratos e escopo de serviço" },
  ],
  lineage: "Ver a linhagem dbt",
  lineageAlt: "Linhagem dbt do manifest versionado: fontes, silver e gold",
  lineageNote: "Snapshot da linhagem; não é o estado do banco em tempo real.",
  sources: "Fontes e rastreabilidade",
  sourcesBody:
    "Cada valor aponta para sua fonte versionada. As proporções são arredondadas na exibição; denominadores e precisão original são preservados no snapshot agregado.",
  viewSource: "Abrir arquivo fonte",
  hash: "SHA-256 do arquivo",
  sourceCommit: "Commit da fonte",
};
