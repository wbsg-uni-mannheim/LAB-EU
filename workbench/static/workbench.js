const strings = {
  de: {
    title: "Study Workbench",
    intro: "Eine Modellstudie konfigurieren und alle Fälle nacheinander bearbeiten.",
    guideEyebrow: "So funktioniert die Studie",
    guideHeading: "Vier Schritte – ohne Programmierkenntnisse",
    guideIntro: "Sie führen dasselbe KI-System nacheinander durch mehrere juristische Fälle. Die Anwendung speichert die Einstellungen und jede Antwort, damit die Ergebnisse später einheitlich ausgewertet werden können.",
    guideStep1Title: "1. Studie einmalig einrichten",
    guideStep1Text: "Tragen Sie einen verständlichen Studiennamen, das getestete Modell und die Sprache der Fälle ein. Geben Sie außerdem an, ob Sie ein einzelnes Sprachmodell oder einen Agenten testen und welche Hilfsmittel verwendet werden.",
    guideStep2Title: "2. System-Prompt festlegen",
    guideStep2Text: "Der System-Prompt enthält die allgemeinen Anweisungen, die bei jedem Fall gleich bleiben. Prüfen und bearbeiten Sie ihn vor dem Start sorgfältig. Er wird exakt gespeichert und dokumentiert.",
    guideStep3Title: "3. Fälle nacheinander bearbeiten",
    guideStep3Text: "Die Anwendung verbindet den System-Prompt automatisch mit dem aktuellen Fall. Kopieren Sie den vollständigen Prompt mit einem Klick in Ihr KI-System. Fügen Sie anschließend die vollständige Antwort unverändert zurück in die Anwendung ein. Nach dem Speichern erscheint automatisch der nächste Fall.",
    guideStep4Title: "4. Studie abschließen",
    guideStep4Text: "Sie können jederzeit unterbrechen und später fortfahren oder nach mindestens einer Antwort vorzeitig abgeben. Nach dem regulären oder vorzeitigen Abschluss kann die Studie – soweit Rubriken vorhanden sind – mit den LAB-EU Judges ausgewertet und über GitHub eingereicht werden.",
    important: "Wichtig:",
    guideNote: "Verwenden Sie während einer Studie immer dasselbe Modell, denselben System-Prompt und dieselben zugelassenen Hilfsmittel. Verändern Sie die KI-Antwort nicht und fügen Sie keine vertraulichen Mandantendaten ein.",
    setupHeading: "Studie konfigurieren",
    studyName: "Studienname",
    model: "Modell",
    studyLanguage: "Sprache der Fälle",
    reviewer: "Durchführende Person",
    provider: "Anbieter",
    executionType: "Ausführungstyp",
    singleLlm: "Single LLM",
    singleLlmHelp: "Das Modell erhält den Prompt und erzeugt unmittelbar eine Antwort, ohne selbstständig mehrere Arbeitsschritte oder Werkzeuge auszuführen.",
    agent: "Agent",
    agentHelp: "Das System kann selbstständig Zwischenschritte planen, Werkzeuge aufrufen oder mehrere Modellaufrufe miteinander verbinden.",
    resources: "Verwendete Ressourcen",
    webSearch: "Websuche",
    webSearchHelp: "Das System kann öffentlich zugängliche Internetseiten oder Suchmaschinen zur Bearbeitung des Falls nutzen.",
    databases: "Datenbanken",
    databasesHelp: "Das System kann juristische Fachdatenbanken, interne Wissensbestände oder andere strukturierte Datenquellen abfragen.",
    otherTools: "Weitere Tools",
    otherToolsHelp: "Das System verwendet zusätzliche Funktionen, etwa Dokumentenanalyse, Rechenwerkzeuge, Codeausführung oder Dateizugriff.",
    systemUnknown: "Bei diesem System nicht bekannt",
    systemUnknownHelp: "Wählen Sie dies, wenn Sie nicht zuverlässig feststellen können, ob das System als Agent arbeitet oder auf Websuche, Datenbanken oder andere Werkzeuge zugreift.",
    systemPrompt: "System-Prompt",
    systemPromptHelp: "Dies ist der LAB-EU-Standardprompt. Er untersagt externe Quellen. Wenn die Studie Websuche oder Datenbanken erlaubt, passen Sie diese Einschränkung vor dem Start ausdrücklich an.",
    judgeOnly: "Nur Fälle mit vorhandener Judge-Rubrik verwenden",
    startStudy: "Studie starten",
    resumeStudy: "Vorhandene Studie fortsetzen",
    resume: "Fortsetzen",
    storedSystemPrompt: "Gespeicherter System-Prompt",
    currentCase: "Aktueller Fall",
    copyCombined: "Gesamten Prompt kopieren",
    combinedPrompt: "Vollständiger Prompt",
    combinedPromptHelp: "Der folgende Text enthält bereits den System-Prompt und den aktuellen Fall. Kopieren Sie ihn einmal vollständig in Ihr KI-System.",
    answer: "Modellantwort (Markdown)",
    clearDraft: "Entwurf löschen",
    confidentiality: "Ich bestätige, dass die Antwort keine vertraulichen Mandantendaten enthält.",
    saveNext: "Antwort speichern und nächsten Fall öffnen",
    endEarly: "Studie vorzeitig abgeben",
    endEarlyHelp: "Nach mindestens einer gespeicherten Antwort können Sie vorzeitig abgeben. Der aktuelle und alle folgenden Fälle werden als nicht bearbeitet dokumentiert.",
    endEarlyConfirm: "Möchten Sie die Studie wirklich vorzeitig abschließen? Offene Fälle können danach nicht mehr bearbeitet werden.",
    endedEarly: "Studie vorzeitig abgeschlossen",
    unanswered: "nicht bearbeitete Fälle",
    completeHeading: "Studie abgeschlossen",
    baseBranch: "Zielbranch",
    createPr: "Branch pushen und Pull Request erstellen",
    gitConfirm: "Ich bestätige Branch, Commit und gegebenenfalls Pull Request.",
    submit: "Studie committen und einreichen",
    dirtyHint: "Bei anderen Änderungen im Repository wird die Einreichung automatisch blockiert.",
    chars: "Zeichen",
    copied: "Kopiert.",
    saved: "Antwort gespeichert.",
    started: "Studie gestartet.",
    draftCleared: "Entwurf gelöscht.",
    judgeReady: "Judge bereit",
    noRubric: "Keine Judge-Rubrik",
    noJudgeCommand: "Die Studie enthält Fälle ohne Rubrik und kann nicht als Ganzes gejudged werden.",
    ready: "Git-Einreichung bereit",
    blocked: "Git-Einreichung blockiert",
    completed: "abgeschlossen",
    scopeCount: "{count} Fälle, davon {judge} mit Judge-Rubrik"
  },
  fr: {
    title: "Espace d'étude",
    intro: "Configurez une étude de modèle et traitez tous les cas successivement.",
    guideEyebrow: "Déroulement de l'étude",
    guideHeading: "Quatre étapes, sans connaissances techniques",
    guideIntro: "Vous soumettez successivement plusieurs cas juridiques au même système d'IA. L'application enregistre la configuration et chaque réponse afin de permettre une évaluation uniforme des résultats.",
    guideStep1Title: "1. Configurer l'étude une seule fois",
    guideStep1Text: "Indiquez un nom d'étude compréhensible, le modèle testé et la langue des cas. Précisez également si vous testez un modèle unique ou un agent, ainsi que les ressources qu'il peut utiliser.",
    guideStep2Title: "2. Définir le prompt système",
    guideStep2Text: "Le prompt système contient les instructions générales qui restent identiques pour tous les cas. Vérifiez-le et modifiez-le soigneusement avant de commencer. Il sera enregistré exactement tel quel.",
    guideStep3Title: "3. Traiter les cas successivement",
    guideStep3Text: "L'application associe automatiquement le prompt système au cas actuel. Copiez le prompt complet en une seule fois dans votre système d'IA. Collez ensuite la réponse complète et non modifiée dans l'application. Le cas suivant apparaît automatiquement après l'enregistrement.",
    guideStep4Title: "4. Terminer l'étude",
    guideStep4Text: "Vous pouvez interrompre l'étude et la reprendre ultérieurement, ou la soumettre avant la fin après au moins une réponse. Après une fin normale ou anticipée, elle peut, lorsque des grilles existent, être évaluée par les juges LAB-EU et soumise via GitHub.",
    important: "Important :",
    guideNote: "Utilisez toujours le même modèle, le même prompt système et les mêmes ressources autorisées pendant toute l'étude. Ne modifiez pas la réponse de l'IA et n'insérez aucune donnée confidentielle de client.",
    setupHeading: "Configurer l'étude",
    studyName: "Nom de l'étude",
    model: "Modèle",
    studyLanguage: "Langue des cas",
    reviewer: "Responsable de l'étude",
    provider: "Fournisseur",
    executionType: "Type d'exécution",
    singleLlm: "LLM unique",
    singleLlmHelp: "Le modèle reçoit le prompt et produit directement une réponse, sans organiser de manière autonome plusieurs étapes ni utiliser d'outils.",
    agent: "Agent",
    agentHelp: "Le système peut planifier lui-même des étapes intermédiaires, appeler des outils ou enchaîner plusieurs appels de modèle.",
    resources: "Ressources utilisées",
    webSearch: "Recherche web",
    webSearchHelp: "Le système peut consulter des sites internet publics ou des moteurs de recherche pour traiter le cas.",
    databases: "Bases de données",
    databasesHelp: "Le système peut interroger des bases juridiques, des connaissances internes ou d'autres sources de données structurées.",
    otherTools: "Autres outils",
    otherToolsHelp: "Le système utilise d'autres fonctions, par exemple l'analyse de documents, le calcul, l'exécution de code ou l'accès à des fichiers.",
    systemUnknown: "Fonctionnement de ce système inconnu",
    systemUnknownHelp: "Choisissez cette option si vous ne pouvez pas déterminer de manière fiable si le système agit comme un agent ou utilise la recherche web, des bases de données ou d'autres outils.",
    systemPrompt: "Prompt système",
    systemPromptHelp: "Il s'agit du prompt standard LAB-EU, qui interdit les sources externes. Si l'étude autorise la recherche web ou des bases de données, adaptez explicitement cette restriction avant de commencer.",
    judgeOnly: "Utiliser uniquement les cas disposant d'une grille de juge",
    startStudy: "Démarrer l'étude",
    resumeStudy: "Reprendre une étude existante",
    resume: "Reprendre",
    storedSystemPrompt: "Prompt système enregistré",
    currentCase: "Cas actuel",
    copyCombined: "Copier le prompt complet",
    combinedPrompt: "Prompt complet",
    combinedPromptHelp: "Le texte suivant contient déjà le prompt système et le cas actuel. Copiez-le intégralement en une seule fois dans votre système d'IA.",
    answer: "Réponse du modèle (Markdown)",
    clearDraft: "Effacer le brouillon",
    confidentiality: "Je confirme que la réponse ne contient aucune donnée confidentielle de client.",
    saveNext: "Enregistrer et ouvrir le cas suivant",
    endEarly: "Soumettre l'étude avant la fin",
    endEarlyHelp: "Après au moins une réponse enregistrée, vous pouvez soumettre l'étude avant la fin. Le cas actuel et tous les cas suivants seront documentés comme non traités.",
    endEarlyConfirm: "Voulez-vous vraiment terminer l'étude avant la fin ? Les cas restants ne pourront plus être traités.",
    endedEarly: "Étude terminée avant la fin",
    unanswered: "cas non traités",
    completeHeading: "Étude terminée",
    baseBranch: "Branche cible",
    createPr: "Pousser la branche et créer une pull request",
    gitConfirm: "Je confirme la branche, le commit et, le cas échéant, la pull request.",
    submit: "Committer et soumettre l'étude",
    dirtyHint: "La soumission est bloquée automatiquement si le dépôt contient d'autres modifications.",
    chars: "caractères",
    copied: "Copié.",
    saved: "Réponse enregistrée.",
    started: "Étude démarrée.",
    draftCleared: "Brouillon effacé.",
    judgeReady: "Juge disponible",
    noRubric: "Pas de grille de juge",
    noJudgeCommand: "L'étude contient des cas sans grille et ne peut pas être évaluée globalement.",
    ready: "Soumission Git prête",
    blocked: "Soumission Git bloquée",
    completed: "terminés",
    scopeCount: "{count} cas, dont {judge} avec une grille de juge"
  }
};

const state = {
  language: localStorage.getItem("workbench-language") || "de",
  study: null,
  studies: [],
  tasks: []
};
const $ = (id) => document.getElementById(id);
const t = (key) => strings[state.language][key] || key;

function notice(message, error = false) {
  const element = $("notice");
  element.textContent = message;
  element.classList.toggle("error", error);
  element.classList.remove("hidden");
  window.clearTimeout(notice.timer);
  notice.timer = window.setTimeout(() => element.classList.add("hidden"), 6000);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function applyLanguage() {
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll(".language").forEach((node) => {
    node.classList.toggle("active", node.dataset.language === state.language);
  });
  updateCount();
  updateScopeCount();
  renderStudies();
}

function draftKey() {
  const task = state.study && state.study.current_task;
  return task ? `lab-eu-study-draft:${state.study.study_id}:${task.task_id}` : "";
}

function updateCount() {
  $("answer-count").textContent = `${$("answer").value.length} ${t("chars")}`;
}

function updateScopeCount() {
  const language = $("study-language").value;
  const tasks = state.tasks.filter((task) => task.language === language);
  const judgeReady = tasks.filter((task) => task.judge_ready).length;
  const selected = $("judge-ready-only").checked ? judgeReady : tasks.length;
  $("scope-count").textContent = t("scopeCount")
    .replace("{count}", selected)
    .replace("{judge}", judgeReady);
}

function renderStudies() {
  const selected = $("study-select").value;
  $("study-select").replaceChildren(new Option("–", ""));
  state.studies.forEach((study) => {
    const progress = `${study.n_completed}/${study.n_tasks}`;
    const suffix = study.ended_early ? ` · ${t("endedEarly")}` : "";
    $("study-select").add(new Option(`${study.study_name} · ${study.model} · ${progress}${suffix}`, study.study_id));
  });
  if (state.studies.some((study) => study.study_id === selected)) $("study-select").value = selected;
}

async function refreshStudies() {
  const data = await api("/api/studies");
  state.studies = data.studies;
  renderStudies();
}

async function refreshTasks() {
  const data = await api("/api/tasks");
  state.tasks = data.tasks;
  updateScopeCount();
}

function renderDocuments(documents) {
  const container = $("documents");
  container.replaceChildren();
  documents.forEach((item) => {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    const pre = document.createElement("pre");
    summary.textContent = item.path;
    pre.textContent = item.content;
    details.append(summary, pre);
    container.append(details);
  });
}

async function renderStudy(study) {
  state.study = study;
  $("study-section").classList.remove("disabled");
  $("active-study-name").textContent = study.study_name;
  const capabilityLabels = {
    agent: t("agent"),
    single_llm: t("singleLlm"),
    web_search: t("webSearch"),
    databases: t("databases"),
    other_tools: t("otherTools"),
    system_unknown: t("systemUnknown")
  };
  const capabilityNames = Object.entries(study.capabilities)
    .filter(([, enabled]) => enabled)
    .map(([name]) => capabilityLabels[name] || name);
  $("study-meta").textContent = `${study.model} · ${study.language.toUpperCase()} · ${capabilityNames.join(", ")}`;
  $("progress").textContent = `${study.n_completed}/${study.n_tasks} ${t("completed")}`;
  $("progress-bar").style.width = `${study.n_tasks ? (study.n_completed / study.n_tasks) * 100 : 0}%`;
  $("end-early").disabled = study.n_completed === 0 || study.complete;
  $("stored-system-prompt").value = study.system_prompt;
  $("system-prompt-hash").textContent = `SHA-256: ${study.system_prompt_sha256}`;

  if (study.complete) {
    $("case-section").classList.add("disabled");
    $("complete-section").classList.remove("disabled");
    document.querySelector("#complete-section h2").textContent = study.ended_early
      ? t("endedEarly")
      : t("completeHeading");
    await renderCompletion();
    return;
  }

  $("complete-section").classList.add("disabled");
  $("case-section").classList.remove("disabled");
  const task = study.current_task;
  $("case-title").textContent = task.title;
  $("case-meta").textContent = `${task.task_id} · ${task.deliverable} · ${task.judge_ready ? t("judgeReady") : t("noRubric")}`;
  renderDocuments(task.documents);
  $("combined-prompt").value = task.combined_prompt;
  $("combined-prompt-hash").textContent = `SHA-256: ${task.combined_prompt_sha256}`;
  $("answer").value = localStorage.getItem(draftKey()) || "";
  $("confidentiality").checked = false;
  updateCount();
}

async function startStudy() {
  try {
    const payload = {
      name: $("study-name").value,
      model: $("model").value,
      language: $("study-language").value,
      reviewer: $("reviewer").value,
      provider: $("provider").value,
      system_prompt: $("system-prompt").value,
      judge_ready_only: $("judge-ready-only").checked,
      capabilities: {
        agent: $("agent").checked,
        single_llm: $("single-llm").checked,
        web_search: $("web-search").checked,
        databases: $("databases").checked,
        other_tools: $("other-tools").checked,
        system_unknown: $("system-unknown").checked
      }
    };
    const study = await api("/api/studies", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Workbench-Token": window.WORKBENCH_TOKEN},
      body: JSON.stringify(payload)
    });
    await refreshStudies();
    await renderStudy(study);
    notice(t("started"));
    $("study-section").scrollIntoView({behavior: "smooth"});
  } catch (error) {
    notice(error.message, true);
  }
}

async function resumeStudy() {
  const studyId = $("study-select").value;
  if (!studyId) return;
  try {
    await renderStudy(await api(`/api/studies/${encodeURIComponent(studyId)}`));
    $("study-section").scrollIntoView({behavior: "smooth"});
  } catch (error) {
    notice(error.message, true);
  }
}

async function saveNext() {
  if (!state.study || !state.study.current_task) return;
  const oldDraftKey = draftKey();
  try {
    const study = await api(`/api/studies/${encodeURIComponent(state.study.study_id)}/answers`, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Workbench-Token": window.WORKBENCH_TOKEN},
      body: JSON.stringify({
        task_id: state.study.current_task.task_id,
        response: $("answer").value,
        confidentiality_confirmed: $("confidentiality").checked
      })
    });
    localStorage.removeItem(oldDraftKey);
    await refreshStudies();
    await renderStudy(study);
    notice(t("saved"));
    $("study-section").scrollIntoView({behavior: "smooth"});
  } catch (error) {
    notice(error.message, true);
  }
}

async function endEarly() {
  if (!state.study || state.study.complete) return;
  if (!window.confirm(t("endEarlyConfirm"))) return;
  try {
    const study = await api(`/api/studies/${encodeURIComponent(state.study.study_id)}/end-early`, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Workbench-Token": window.WORKBENCH_TOKEN},
      body: JSON.stringify({confirmed: true})
    });
    if (draftKey()) localStorage.removeItem(draftKey());
    await refreshStudies();
    await renderStudy(study);
    notice(t("endedEarly"));
    $("complete-section").scrollIntoView({behavior: "smooth"});
  } catch (error) {
    notice(error.message, true);
  }
}

async function renderCompletion() {
  try {
    const readiness = await api(`/api/git-status?run_dir=${encodeURIComponent(state.study.run_dir_relative)}`);
    const gitStatus = readiness.ready
      ? t("ready")
      : `${t("blocked")}: ${readiness.unrelated_changes.slice(0, 5).join(", ")}`;
    const judge = state.study.judge_command || t("noJudgeCommand");
    const early = state.study.ended_early
      ? `${t("endedEarly")}: ${state.study.n_remaining} ${t("unanswered")}\n`
      : "";
    $("study-result").textContent = `${early}${state.study.run_dir_relative}\n${judge}\n${gitStatus}`;
  } catch (error) {
    $("study-result").textContent = error.message;
  }
}

async function submitGit() {
  if (!state.study || !state.study.complete) return;
  if (!window.confirm(t("submit"))) return;
  try {
    const result = await api("/api/submit", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Workbench-Token": window.WORKBENCH_TOKEN},
      body: JSON.stringify({
        run_dir: state.study.run_dir_relative,
        task_id: state.study.study_name,
        reviewer: state.study.reviewer || "reviewer",
        base_branch: $("base-branch").value,
        create_pull_request: $("create-pr").checked,
        git_confirmed: $("git-confirm").checked
      })
    });
    $("study-result").textContent = `${result.branch}\n${result.commit}${result.pull_request_url ? `\n${result.pull_request_url}` : ""}`;
    notice(result.pull_request_url || result.commit);
  } catch (error) {
    notice(error.message, true);
  }
}

document.querySelectorAll(".language").forEach((button) => {
  button.addEventListener("click", () => {
    state.language = button.dataset.language;
    localStorage.setItem("workbench-language", state.language);
    applyLanguage();
  });
});

$("study-language").addEventListener("change", () => {
  updateScopeCount();
});
$("judge-ready-only").addEventListener("change", updateScopeCount);
$("system-unknown").addEventListener("change", () => {
  const unknown = $("system-unknown").checked;
  ["single-llm", "agent", "web-search", "databases", "other-tools"].forEach((id) => {
    $(id).disabled = unknown;
  });
  if (unknown) {
    $("single-llm").checked = false;
    $("agent").checked = false;
    $("web-search").checked = false;
    $("databases").checked = false;
    $("other-tools").checked = false;
  } else {
    $("single-llm").checked = true;
  }
});
$("start-study").addEventListener("click", startStudy);
$("resume-study").addEventListener("click", resumeStudy);
$("copy-combined-prompt").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("combined-prompt").value);
    notice(t("copied"));
  } catch (error) {
    $("combined-prompt").select();
    notice(error.message, true);
  }
});
$("answer").addEventListener("input", () => {
  updateCount();
  if (draftKey()) localStorage.setItem(draftKey(), $("answer").value);
});
$("clear-draft").addEventListener("click", () => {
  if (draftKey()) localStorage.removeItem(draftKey());
  $("answer").value = "";
  updateCount();
  notice(t("draftCleared"));
});
$("save-next").addEventListener("click", saveNext);
$("end-early").addEventListener("click", endEarly);
$("submit-git").addEventListener("click", submitGit);

$("system-prompt").value = window.DEFAULT_STUDY_SYSTEM_PROMPT;
applyLanguage();
Promise.all([refreshStudies(), refreshTasks()]).catch((error) => notice(error.message, true));
