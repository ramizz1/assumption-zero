import fs from "node:fs";
import path from "node:path";

const projectRoot = "C:/Users/user/Desktop/idea/assumption-zero";
const uaDir = `${projectRoot}/.ua`;
const extraction = JSON.parse(fs.readFileSync(`${uaDir}/tmp/ua-file-extract-results-5.json`, "utf8"));
const batches = JSON.parse(fs.readFileSync(`${uaDir}/intermediate/batches.json`, "utf8"));
const batch = batches.batches.find((entry) => entry.batchIndex === 5);
if (!batch) throw new Error("Batch 5 not found");

const fileSummaries = {
  "backend/assumption_zero/__init__.py": "Defines the Assumption Zero Python package metadata and exposes the installed application version.",
  "backend/assumption_zero/analysis/unit_economics.py": "Implements the transparent subscription unit-economics model shared by CLI and web-facing simulations, including breakeven, payback, LTV, and health classification.",
  "backend/assumption_zero/cli.py": "Provides the full Typer command-line interface for configuring providers, running and reviewing analyses, simulating unit economics, and exporting richly formatted reports.",
  "backend/assumption_zero/main.py": "Creates and configures the FastAPI application, including clean validation errors, constrained CORS, API routes, startup storage initialization, and root metadata.",
  "backend/assumption_zero/storage.py": "Implements human-readable file persistence for analysis metadata, inputs, and results using CSV plus JSON, with atomic writes and one-time legacy migration.",
  "backend/tests/test_api.py": "Exercises FastAPI health, analysis, demo, and listing endpoints, including secret redaction and request-bound validation behavior.",
  "backend/tests/test_cli_parity.py": "Checks that CLI commands and provider controls match web capabilities and that CLI runs share storage, filtering, and unit-economics behavior with the web application.",
  "backend/tests/test_export.py": "Validates Markdown, HTML, and JSON analysis exports for required verdict, evidence, experiment, competitor, disclaimer, and secret-safety content.",
  "backend/tests/test_validation_errors.py": "Covers clean API validation messages, provider-key verification, release-mode debug parsing, and SSRF URL filtering safeguards."
};

const fileTags = {
  "backend/assumption_zero/__init__.py": ["entry-point", "package-metadata", "versioning"],
  "backend/assumption_zero/analysis/unit_economics.py": ["unit-economics", "calculation", "validation", "data-model"],
  "backend/assumption_zero/cli.py": ["entry-point", "cli", "reporting", "serialization", "configuration"],
  "backend/assumption_zero/main.py": ["entry-point", "api-handler", "middleware", "validation", "startup"],
  "backend/assumption_zero/storage.py": ["storage", "persistence", "serialization", "migration", "file-io"],
  "backend/tests/test_api.py": ["test", "api-handler", "integration", "validation", "security"],
  "backend/tests/test_cli_parity.py": ["test", "cli", "integration", "regression", "feature-parity"],
  "backend/tests/test_export.py": ["test", "serialization", "reporting", "regression", "security"],
  "backend/tests/test_validation_errors.py": ["test", "validation", "security", "api-handler", "regression"]
};

const summaries = {
  UnitEconomicsResult: "Carries normalized unit-economics inputs, derived subscription metrics, and the resulting health label as an immutable record.",
  extract_price: "Extracts the first numeric amount from optional text and falls back to a supplied default when no usable value is present.",
  calculate_unit_economics: "Validates model inputs and calculates gross margin, churn-adjusted contribution, breakeven customers, CAC payback, LTV, LTV-to-CAC ratio, and health.",
  _score_color: "Maps opportunity-score thresholds to Rich terminal color styles.",
  _score_bar: "Renders a bounded opportunity score as a colored terminal progress bar with an optional numeric ratio.",
  _rec_color: "Maps recommendation labels to their terminal emphasis colors.",
  _status_color: "Maps persisted analysis statuses to Rich terminal styles.",
  _conf_color: "Maps evidence-confidence labels to terminal colors.",
  _perspective_color: "Assigns distinct terminal colors to the supported analysis perspectives.",
  _print_splash: "Prints the branded CLI banner, feature summary, repository link, and configuration tip.",
  _print_section: "Prints a consistently styled terminal section divider.",
  _print_disclaimer: "Displays the product's decision-support disclaimer in a highlighted terminal panel.",
  _build_engine_sync: "Builds the synchronous CLI analysis stack from runtime provider overrides, an LLM adapter, research providers, and the analysis engine.",
  _run_analysis_sync: "Persists a new run, executes the asynchronous analysis engine with live progress reporting, and records either the completed result or failure.",
  _clean_summary: "Normalizes generated summaries for terminal display by removing broken Markdown table syntax and preserving readable content.",
  _print_report: "Renders the complete analysis report in the terminal, including verdict, scores, evidence, competitors, perspectives, disagreements, experiments, and founder actions.",
  _export_markdown: "Serializes a complete analysis result into a structured Markdown report with evidence citations, competitor intelligence, experiments, and disclaimer.",
  _export_html: "Generates a standalone styled HTML analysis report covering the executive verdict, score breakdown, evidence, competitors, perspectives, and next steps.",
  _ask_idea: "Runs an interactive questionnaire that gathers the required and optional fields for an IdeaInput model.",
  _with_founder_context: "Applies non-empty command-line founder-context overrides to a validated idea without discarding existing fields.",
  _ask_idea_with_key: "Runs the interactive idea wizard together with AI provider, key, model, and base-URL selection.",
  guide: "Displays practical guidance for writing a concrete startup idea that produces actionable validation results.",
  analyze: "Accepts structured files, freeform prompts, interactive input, provider settings, and founder context before running and printing an analysis.",
  prompt: "Parses a natural-language idea from an argument or file, applies founder context and provider options, then runs the analysis.",
  demo: "Runs the built-in demonstration idea through the selected provider and research depth, then prints the report.",
  simulate: "Loads a saved analysis and calculates an adjustable subscription unit-economics scenario for terminal display.",
  verify_provider: "Validates a requested AI provider configuration and connectivity using the same safeguards and adapter construction as web settings.",
  list_cmd: "Lists recent analyses with optional text, status, or verdict filtering and concise terminal status details.",
  config_cmd: "Guides the user through interactive environment configuration and saves selected API keys and provider settings to an env file.",
  show: "Resolves a saved analysis identifier and renders its full persisted report.",
  export: "Exports a saved analysis as Markdown, JSON, or HTML to stdout or a chosen file.",
  delete: "Resolves, confirms, and deletes one persisted analysis and its associated input and result files.",
  clean: "Bulk-removes persisted analyses matching selected statuses after optional confirmation.",
  serve: "Starts the FastAPI backend with configurable host, port, and development reload behavior.",
  version: "Displays the installed version and currently resolved AI and research provider configuration.",
  clean_error_message: "Removes Pydantic boilerplate, type metadata, and documentation URLs from validation messages returned to API clients.",
  create_app: "Constructs the FastAPI application with exception handlers, CORS, routes, storage startup initialization, and root product metadata.",
  _ensure_dirs: "Creates the storage directories and initiates the one-time legacy-data migration.",
  _migrate_legacy_storage: "Merges legacy CSV rows and JSON artifacts into the configured store without overwriting newer data or blocking startup on migration errors.",
  _read_all: "Ensures storage exists and reads every analysis metadata row from CSV.",
  _write_all: "Atomically rewrites the analysis metadata CSV through a temporary file.",
  resolve_id: "Resolves a full analysis UUID, short prefix, or one-based list index to a persisted full identifier.",
  _input_path: "Builds the input JSON path after resolving short analysis identifiers when needed.",
  _result_path: "Builds the result JSON path after resolving short analysis identifiers when needed.",
  create_record: "Writes a new analysis input document and prepends its pending metadata row to storage.",
  update_stage: "Updates the persisted runtime status and analysis stage for an existing record.",
  complete_record: "Atomically writes a completed analysis result and marks its metadata row complete with a timestamp.",
  fail_record: "Marks an analysis failed and stores a bounded error message.",
  get_record: "Returns the metadata row for a resolvable analysis identifier.",
  get_input: "Loads and decodes a persisted analysis input document when present.",
  get_result: "Loads and decodes a persisted completed analysis result when present.",
  list_records: "Returns the newest persisted analysis metadata rows up to a requested limit.",
  delete_record: "Removes an analysis metadata row and its associated input and result JSON files.",
  init_storage: "Initializes required storage directories while preserving the asynchronous startup interface."
};

const testSummaries = {
  client: "Provides a pytest fixture that runs the FastAPI application through a TestClient lifecycle.",
  test_health: "Verifies the health endpoint returns status, version, and configured provider metadata.",
  test_health_no_secrets_exposed: "Ensures health responses never disclose configured API-key or token field names.",
  test_create_analysis_returns_id: "Confirms a valid analysis request is accepted asynchronously and returns a pending analysis identifier.",
  test_get_nonexistent_analysis: "Confirms unknown analysis identifiers return HTTP 404.",
  test_list_analyses_returns_list: "Confirms the analyses collection endpoint returns a JSON list.",
  test_demo_endpoint_returns_id: "Verifies demo creation returns an identifier and forwards an explicit Groq key and provider override.",
  test_demo_auto_uses_browser_groq_key: "Verifies automatic demo selection uses a browser-supplied Groq key when available.",
  test_create_analysis_invalid_input: "Checks that analysis requests missing required idea fields are rejected with HTTP 422.",
  test_input_too_long_rejected: "Checks that idea fields exceeding schema length bounds are rejected.",
  test_prompt_length_and_provider_are_bounded: "Checks both freeform prompt length limits and the allowed AI provider set.",
  test_analysis_list_limit_is_bounded: "Checks that list pagination limits outside the accepted range are rejected.",
  test_cli_exposes_web_equivalent_commands_and_provider_controls: "Asserts CLI help exposes the web-equivalent workflow commands, research controls, provider options, and founder-context flags.",
  test_cli_founder_context_flags_override_parsed_idea: "Verifies CLI founder-context flags replace only the specified fields of a parsed idea.",
  test_unit_economics_matches_web_default_model: "Checks shared unit-economics calculations against the web simulator's expected default scenario.",
  test_cli_analysis_is_saved_for_web_history: "Runs a fake CLI analysis and verifies its metadata and result are available to web history storage.",
  test_history_verdict_filters_work_for_web_and_cli: "Persists a completed recommendation and verifies shared history filtering by verdict and run status.",
  _make_result: "Builds a representative completed AnalysisResult fixture with calculated score, confidence, evidence, and experiments for export tests.",
  test_markdown_export_contains_disclaimer: "Ensures Markdown exports include the decision-support disclaimer.",
  test_markdown_export_contains_idea_name: "Ensures Markdown exports identify the analyzed idea.",
  test_markdown_export_contains_score: "Ensures Markdown exports include the opportunity-score section.",
  test_markdown_export_contains_evidence_ids: "Ensures Markdown exports retain evidence citation identifiers.",
  test_json_export_no_secrets: "Checks serialized analysis JSON does not contain recognizable credential values.",
  test_markdown_export_contains_experiments: "Ensures Markdown exports include generated validation experiments.",
  test_html_export_structure: "Checks standalone HTML exports include their document shell, idea, verdict, score breakdown, and disclaimer.",
  test_exports_include_full_competitor_intelligence: "Ensures Markdown and HTML exports retain verified competitor details, evidence, strengths, complaints, and confidence.",
  test_clean_error_message_helper: "Checks that public error cleanup removes Pydantic metadata while retaining the actionable validation message.",
  test_gibberish_prompt_endpoint_returns_clean_error: "Checks gibberish prompts produce a clean public error without framework boilerplate.",
  test_empty_prompt_returns_clean_error: "Checks whitespace-only prompts return a non-empty clean validation message.",
  test_verify_keys_endpoint_success: "Checks provider verification succeeds for the mock provider and returns a clear status message.",
  test_verify_keys_missing_key_returns_400: "Checks provider verification rejects an empty required API key with HTTP 400.",
  test_release_debug_value_does_not_break_startup: "Checks the release debug value is safely normalized to false during settings construction.",
  test_ssrf_url_filter_blocks_local_and_non_http_targets: "Checks the provider URL guard rejects loopback, metadata-service, and file URLs while allowing a public HTTPS address."
};

function complexityForLines(lines) {
  if (lines > 200) return "complex";
  if (lines >= 50) return "moderate";
  return "simple";
}

function functionTags(filePath, name) {
  if (filePath.includes("/tests/")) {
    if (name === "client") return ["test", "fixture", "api-handler"];
    if (name === "_make_result") return ["test", "factory", "data-model"];
    const domain = filePath.includes("test_api") ? "api-handler" : filePath.includes("test_cli") ? "cli" : filePath.includes("test_export") ? "serialization" : "validation";
    return ["test", "regression", domain];
  }
  if (filePath.endsWith("unit_economics.py")) return name === "UnitEconomicsResult" ? ["data-model", "unit-economics", "immutable"] : ["utility", "unit-economics", "calculation"];
  if (filePath.endsWith("main.py")) return name === "create_app" ? ["factory", "api-handler", "startup"] : ["utility", "validation", "serialization"];
  if (filePath.endsWith("storage.py")) return ["storage", "persistence", name.includes("path") ? "path-resolution" : "file-io"];
  if (["_export_markdown", "_export_html", "export"].includes(name)) return ["serialization", "reporting", "cli-command"];
  if (["analyze", "prompt", "demo", "simulate", "verify_provider", "list_cmd", "config_cmd", "show", "delete", "clean", "serve", "version", "guide"].includes(name)) return ["cli-command", "entry-point", name === "serve" ? "api-handler" : "workflow"];
  if (name.startsWith("_print") || name.includes("color") || name === "_score_bar" || name === "_clean_summary") return ["utility", "terminal-formatting", "reporting"];
  if (name.includes("engine") || name.includes("analysis")) return ["service", "orchestration", "cli"];
  return ["utility", "cli", "validation"];
}

const languageNotes = {
  "backend/assumption_zero/analysis/unit_economics.py": "Uses a frozen dataclass and Optional derived values to represent undefined payback, breakeven, or LTV cases explicitly.",
  "backend/assumption_zero/cli.py": "Combines Typer commands with Rich panels, tables, progress indicators, and lazy imports for a comprehensive terminal application.",
  "backend/assumption_zero/main.py": "Uses a FastAPI application factory with nested exception and startup handlers before exporting a module-level app instance.",
  "backend/assumption_zero/storage.py": "Uses temporary files plus os.replace for atomic CSV and result writes, while JSON payloads remain human-readable.",
  "backend/tests/test_api.py": "Uses pytest fixtures, FastAPI TestClient, and AsyncMock to isolate background analysis execution."
};

const nodes = [];
const edges = [];
const nodeIds = new Set();
const edgeKeys = new Set();
const extractedByPath = new Map(extraction.results.map((entry) => [entry.path, entry]));

function addNode(node) {
  if (nodeIds.has(node.id)) throw new Error(`Duplicate node ${node.id}`);
  nodeIds.add(node.id);
  nodes.push(node);
}

function addEdge(source, target, type, weight) {
  if (source === target) throw new Error(`Self edge ${source}`);
  const key = `${source}|${target}|${type}`;
  if (edgeKeys.has(key)) return;
  edgeKeys.add(key);
  edges.push({ source, target, type, direction: "forward", weight });
}

for (const file of batch.files) {
  const extracted = extractedByPath.get(file.path);
  if (!extracted) throw new Error(`Missing extraction result for ${file.path}`);
  const fileId = `file:${file.path}`;
  const fileNode = {
    id: fileId,
    type: "file",
    name: path.posix.basename(file.path),
    filePath: file.path,
    summary: fileSummaries[file.path],
    tags: fileTags[file.path],
    complexity: complexityForLines(extracted.nonEmptyLines)
  };
  if (languageNotes[file.path]) fileNode.languageNotes = languageNotes[file.path];
  addNode(fileNode);

  const exportedNames = new Set((extracted.exports ?? []).map((item) => item.name));
  for (const cls of extracted.classes ?? []) {
    const lineCount = cls.endLine - cls.startLine + 1;
    if (!(lineCount >= 20 || (cls.methods?.length ?? 0) >= 2 || exportedNames.has(cls.name))) continue;
    const id = `class:${file.path}:${cls.name}`;
    addNode({
      id,
      type: "class",
      name: cls.name,
      filePath: file.path,
      lineRange: [cls.startLine, cls.endLine],
      summary: summaries[cls.name],
      tags: functionTags(file.path, cls.name),
      complexity: complexityForLines(lineCount)
    });
    addEdge(fileId, id, "contains", 1.0);
    if (exportedNames.has(cls.name)) addEdge(fileId, id, "exports", 0.8);
  }

  for (const fn of extracted.functions ?? []) {
    const lineCount = fn.endLine - fn.startLine + 1;
    if (!(lineCount >= 10 || exportedNames.has(fn.name))) continue;
    const id = `function:${file.path}:${fn.name}`;
    const summary = summaries[fn.name] ?? testSummaries[fn.name];
    if (!summary) throw new Error(`Missing summary for ${file.path}:${fn.name}`);
    addNode({
      id,
      type: "function",
      name: fn.name,
      filePath: file.path,
      lineRange: [fn.startLine, fn.endLine],
      summary,
      tags: functionTags(file.path, fn.name),
      complexity: complexityForLines(lineCount)
    });
    addEdge(fileId, id, "contains", 1.0);
    if (exportedNames.has(fn.name)) addEdge(fileId, id, "exports", 0.8);
  }
}

for (const file of batch.files) {
  for (const importedPath of batch.batchImportData[file.path] ?? []) {
    addEdge(`file:${file.path}`, `file:${importedPath}`, "imports", 0.7);
  }
}

// Add deterministic same-file calls when both extracted symbols became nodes.
for (const file of batch.files) {
  const extracted = extractedByPath.get(file.path);
  for (const call of extracted.callGraph ?? []) {
    const source = `function:${file.path}:${call.caller}`;
    const functionTarget = `function:${file.path}:${call.callee}`;
    const classTarget = `class:${file.path}:${call.callee}`;
    if (!nodeIds.has(source)) continue;
    if (nodeIds.has(functionTarget)) addEdge(source, functionTarget, "calls", 0.8);
    else if (nodeIds.has(classTarget)) addEdge(source, classTarget, "calls", 0.8);
  }
}

// Confident cross-file calls supported by same-part nodes or neighborMap symbols.
const semanticCalls = [
  ["function:backend/assumption_zero/main.py:create_app", "function:backend/assumption_zero/config.py:get_settings"],
  ["function:backend/assumption_zero/main.py:create_app", "function:backend/assumption_zero/storage.py:init_storage"],
  ["function:backend/tests/test_cli_parity.py:test_history_verdict_filters_work_for_web_and_cli", "function:backend/assumption_zero/services/analysis_service.py:list_analyses"],
  ["function:backend/tests/test_cli_parity.py:test_cli_analysis_is_saved_for_web_history", "class:backend/assumption_zero/schemas.py:AnalysisResult"],
  ["function:backend/tests/test_export.py:_make_result", "class:backend/assumption_zero/schemas.py:AnalysisResult"],
  ["function:backend/tests/test_export.py:test_exports_include_full_competitor_intelligence", "class:backend/assumption_zero/schemas.py:Competitor"],
  ["function:backend/tests/test_validation_errors.py:test_release_debug_value_does_not_break_startup", "class:backend/assumption_zero/config.py:Settings"],
  ["function:backend/tests/test_validation_errors.py:test_ssrf_url_filter_blocks_local_and_non_http_targets", "function:backend/assumption_zero/config.py:is_public_http_url"]
];
for (const [source, target] of semanticCalls) addEdge(source, target, "calls", 0.8);

const expectedImportCount = batch.files.reduce((sum, file) => sum + (batch.batchImportData[file.path]?.length ?? 0), 0);
const actualImportCount = edges.filter((edge) => edge.type === "imports").length;
if (actualImportCount !== expectedImportCount) throw new Error(`Import edge mismatch: expected ${expectedImportCount}, got ${actualImportCount}`);

const partCount = Math.ceil(Math.max(nodes.length / 60, edges.length / 120));
const sortedPaths = batch.files.map((file) => file.path).sort();
const chunkSize = Math.ceil(sortedPaths.length / partCount);
const importedPaths = new Set([
  ...Object.keys(batch.batchImportData),
  ...Object.values(batch.batchImportData).flat(),
  ...Object.keys(batch.neighborMap ?? {}),
  ...Object.values(batch.neighborMap ?? {}).flatMap((items) => items.map((item) => item.path))
]);
const neighborSymbols = new Map();
for (const neighbors of Object.values(batch.neighborMap ?? {})) {
  for (const neighbor of neighbors) neighborSymbols.set(neighbor.path, new Set(neighbor.symbols));
}

function edgeEndpointAllowed(id, partNodeIds) {
  if (partNodeIds.has(id)) return true;
  if (id.startsWith("file:")) return importedPaths.has(id.slice(5));
  const match = id.match(/^(function|class):(.+):([^:]+)$/);
  return Boolean(match && neighborSymbols.get(match[2])?.has(match[3]));
}

let totalWrittenNodes = 0;
let totalWrittenEdges = 0;
for (let index = 0; index < partCount; index += 1) {
  const group = new Set(sortedPaths.slice(index * chunkSize, (index + 1) * chunkSize));
  const partNodes = nodes.filter((node) => group.has(node.filePath));
  const partNodeIds = new Set(partNodes.map((node) => node.id));
  const partEdges = edges.filter((edge) => partNodeIds.has(edge.source));
  for (const edge of partEdges) {
    if (!edgeEndpointAllowed(edge.source, partNodeIds) || !edgeEndpointAllowed(edge.target, partNodeIds)) {
      throw new Error(`Part ${index + 1} edge validation failed: ${edge.source} -> ${edge.target}`);
    }
  }
  const outputPath = `${uaDir}/intermediate/batch-5-part-${index + 1}.json`;
  fs.writeFileSync(outputPath, `${JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2)}\n`, "utf8");
  JSON.parse(fs.readFileSync(outputPath, "utf8"));
  totalWrittenNodes += partNodes.length;
  totalWrittenEdges += partEdges.length;
}

if (totalWrittenNodes !== nodes.length || totalWrittenEdges !== edges.length) {
  throw new Error(`Partition mismatch: nodes ${totalWrittenNodes}/${nodes.length}, edges ${totalWrittenEdges}/${edges.length}`);
}
console.log(JSON.stringify({ partCount, nodeCount: nodes.length, edgeCount: edges.length, importCount: actualImportCount, filesSkipped: extraction.filesSkipped }));
