import fs from 'node:fs';
import path from 'node:path';

const projectRoot = 'C:/Users/user/Desktop/idea/assumption-zero';
const uaDir = path.join(projectRoot, '.ua');
const input = JSON.parse(fs.readFileSync(path.join(uaDir, 'tmp/ua-file-analyzer-input-4.json'), 'utf8'));
const extraction = JSON.parse(fs.readFileSync(path.join(uaDir, 'tmp/ua-file-extract-results-4.json'), 'utf8'));
const batches = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate/batches.json'), 'utf8'));
const batch = batches.batches.find((item) => item.batchIndex === 4);

const fileMeta = {
  'backend/assumption_zero/llm/__init__.py': ['Defines the public LLM package surface by re-exporting the adapter interface and supported provider implementations.', ['entry-point', 'barrel', 'llm-adapter']],
  'backend/assumption_zero/llm/base.py': ['Defines validated LLM output models, discipline-specific system prompts, evidence-grounded prompt construction, and the abstract provider adapter contract with default idea parsing.', ['llm-adapter', 'prompt-engineering', 'data-model']],
  'backend/assumption_zero/llm/beta_adapter.py': ['Implements the legacy Beta provider as a configured OpenRouter alias without bundling a shared credential.', ['llm-adapter', 'openrouter', 'compatibility']],
  'backend/assumption_zero/llm/fallback_adapter.py': ['Orchestrates an ordered provider chain, failing over on provider errors and falling back to deterministic analysis when no configured adapter is available.', ['llm-adapter', 'failover', 'resilience']],
  'backend/assumption_zero/llm/groq_adapter.py': ['Connects the analysis contract to Groq chat completions, including model fallback, structured perspective parsing, clarification, and raw-prompt extraction.', ['llm-adapter', 'groq', 'http-client']],
  'backend/assumption_zero/llm/hybrid_adapter.py': ['Balances perspective workloads between Groq and OpenRouter and performs automatic cross-provider failover for analysis, clarification, and prompt parsing.', ['llm-adapter', 'provider-routing', 'failover']],
  'backend/assumption_zero/llm/mock_adapter.py': ['Provides the labeled deterministic evidence engine, deriving opportunity scores, findings, risks, and recommendations from collected evidence without inventing model output.', ['llm-adapter', 'deterministic-scoring', 'fallback']],
  'backend/assumption_zero/llm/ollama_adapter.py': ['Runs analysis against local Ollama models, supporting both OpenAI-compatible chat completions and Ollama native chat endpoints.', ['llm-adapter', 'ollama', 'local-model']],
  'backend/assumption_zero/llm/openai_compat_adapter.py': ['Supports configurable OpenAI-compatible chat-completion providers with structured response parsing, recommendation normalization, and provider-specific authentication.', ['llm-adapter', 'openai-compatible', 'http-client']],
  'backend/assumption_zero/llm/opencode_adapter.py': ['Connects analysis and prompt parsing to the configurable OpenCode API using shared prompt and output-normalization logic.', ['llm-adapter', 'opencode', 'http-client']],
  'backend/assumption_zero/llm/openrouter_adapter.py': ['Implements OpenRouter analysis across configurable and fallback models, with robust JSON repair, structured perspective validation, and prompt parsing.', ['llm-adapter', 'openrouter', 'json-repair']],
  'backend/tests/test_llm_adapters.py': ['Tests adapter construction, explicit-provider failure behavior, deterministic raw-prompt parsing, gibberish rejection, and fallback-chain operation.', ['test', 'llm-adapter', 'failover']],
};

const symbolMeta = {
  'backend/assumption_zero/llm/base.py:DiscoveredCompetitor': ['Validates an evidence-grounded competitor candidate and normalizes direct versus indirect classifications.', ['data-model', 'validation', 'competitor-research']],
  'backend/assumption_zero/llm/base.py:PerspectiveOutput': ['Validates the structured result of one model perspective while discarding malformed competitor entries safely.', ['data-model', 'validation', 'analysis-output']],
  'backend/assumption_zero/llm/base.py:build_analysis_prompt': ['Builds a compact evidence-prioritized prompt with idea context, discipline instructions, citation constraints, and the required JSON schema.', ['prompt-engineering', 'evidence', 'serialization']],
  'backend/assumption_zero/llm/base.py:LLMAdapter': ['Defines the asynchronous provider interface and supplies default idea clarification and heuristic raw-prompt structuring.', ['abstract-class', 'llm-adapter', 'adapter-pattern']],
  'backend/assumption_zero/llm/beta_adapter.py:BetaAdapter': ['Exposes OpenRouter behavior under the Beta identifier while requiring the user to supply OpenRouter configuration.', ['llm-adapter', 'openrouter', 'compatibility']],
  'backend/assumption_zero/llm/fallback_adapter.py:FallbackChainAdapter': ['Sequences available adapters, preserves validation errors, translates quota failures, and falls back across analysis and parsing operations.', ['llm-adapter', 'failover', 'resilience']],
  'backend/assumption_zero/llm/groq_adapter.py:GroqAdapter': ['Executes Groq-hosted model calls with credentials, model fallback, shared prompting, and normalized analysis output.', ['llm-adapter', 'groq', 'http-client']],
  'backend/assumption_zero/llm/hybrid_adapter.py:HybridLLMAdapter': ['Routes perspectives between Groq and OpenRouter and retries the alternate provider when the primary fails.', ['llm-adapter', 'provider-routing', 'failover']],
  'backend/assumption_zero/llm/mock_adapter.py:_count': ['Counts evidence items of a requested evidence type.', ['utility', 'evidence', 'aggregation']],
  'backend/assumption_zero/llm/mock_adapter.py:_avg_relevance': ['Calculates average relevance for evidence of a requested type.', ['utility', 'evidence', 'aggregation']],
  'backend/assumption_zero/llm/mock_adapter.py:_high_reliability_count': ['Counts evidence items carrying the highest reliability rating.', ['utility', 'evidence', 'aggregation']],
  'backend/assumption_zero/llm/mock_adapter.py:_compute_scores': ['Derives the seven opportunity dimensions from evidence mix, relevance, reliability, and idea completeness.', ['deterministic-scoring', 'evidence', 'analysis']],
  'backend/assumption_zero/llm/mock_adapter.py:_recommendation_from_avg': ['Maps an average opportunity score to a standardized founder recommendation.', ['deterministic-scoring', 'recommendation', 'utility']],
  'backend/assumption_zero/llm/mock_adapter.py:_findings': ['Generates perspective-specific evidence findings without adding unsupported facts.', ['deterministic-analysis', 'evidence', 'reporting']],
  'backend/assumption_zero/llm/mock_adapter.py:MockAdapter': ['Implements the always-available deterministic provider using evidence-derived scores and clearly labeled template analysis.', ['llm-adapter', 'deterministic-scoring', 'fallback']],
  'backend/assumption_zero/llm/ollama_adapter.py:OllamaAdapter': ['Connects to local Ollama deployments and adapts either supported chat endpoint to the shared analysis contract.', ['llm-adapter', 'ollama', 'local-model']],
  'backend/assumption_zero/llm/openai_compat_adapter.py:_parse_output': ['Parses OpenAI-compatible model text into validated perspective output and normalizes recommendation values.', ['serialization', 'validation', 'llm-output']],
  'backend/assumption_zero/llm/openai_compat_adapter.py:OpenAICompatAdapter': ['Executes analysis through a configurable OpenAI-compatible endpoint and validates its structured response.', ['llm-adapter', 'openai-compatible', 'http-client']],
  'backend/assumption_zero/llm/opencode_adapter.py:OpencodeAdapter': ['Executes OpenCode chat calls for analysis, clarification, and structured idea extraction.', ['llm-adapter', 'opencode', 'http-client']],
  'backend/assumption_zero/llm/openrouter_adapter.py:_repair_and_parse_json': ['Repairs common fenced, truncated, and malformed model JSON before decoding it.', ['json-repair', 'serialization', 'validation']],
  'backend/assumption_zero/llm/openrouter_adapter.py:_parse_output': ['Converts repaired model JSON into a validated perspective result with normalized recommendations.', ['serialization', 'validation', 'llm-output']],
  'backend/assumption_zero/llm/openrouter_adapter.py:OpenRouterAdapter': ['Runs evidence-grounded analysis through OpenRouter with configurable models, fallback models, and structured parsing.', ['llm-adapter', 'openrouter', 'http-client']],
  'backend/tests/test_llm_adapters.py:test_build_all_llm_adapters': ['Verifies every supported provider name builds an adapter exposing availability and model identity.', ['test', 'factory', 'llm-adapter']],
  'backend/tests/test_llm_adapters.py:test_explicit_provider_never_silently_falls_back_to_mock': ['Verifies an unavailable explicitly selected provider raises instead of silently returning the deterministic adapter.', ['test', 'error-handling', 'provider-selection']],
  'backend/tests/test_llm_adapters.py:test_mock_adapter_parse_prompt': ['Verifies deterministic prompt parsing extracts a usable idea name, geography, and competitors.', ['test', 'prompt-parsing', 'mock-adapter']],
  'backend/tests/test_llm_adapters.py:test_gibberish_rejection_in_adapters': ['Verifies adapter prompt parsing rejects meaningless input with a clear validation error.', ['test', 'validation', 'prompt-parsing']],
  'backend/tests/test_llm_adapters.py:test_fallback_chain_adapter': ['Verifies the fallback chain remains available and delegates raw-prompt parsing through its active adapter.', ['test', 'failover', 'llm-adapter']],
};

const resultByPath = new Map(extraction.results.map((item) => [item.path, item]));
const complexityForLines = (lines) => lines > 200 ? 'complex' : lines >= 50 ? 'moderate' : 'simple';
const nodes = [];
const edges = [];

for (const batchFile of input.batchFiles) {
  const result = resultByPath.get(batchFile.path);
  if (!result) throw new Error(`Missing extraction result for ${batchFile.path}`);
  const meta = fileMeta[batchFile.path];
  if (!meta) throw new Error(`Missing file metadata for ${batchFile.path}`);
  nodes.push({
    id: `file:${batchFile.path}`,
    type: 'file',
    name: path.posix.basename(batchFile.path),
    filePath: batchFile.path,
    summary: meta[0],
    tags: meta[1],
    complexity: complexityForLines(result.nonEmptyLines),
    ...(batchFile.path === 'backend/assumption_zero/llm/base.py' ? { languageNotes: 'Uses Pydantic field validators for tolerant model-output ingestion and an ABC to keep asynchronous provider implementations interchangeable.' } : {}),
  });

  const exportNames = new Set((result.exports ?? []).map((item) => item.name));
  for (const [type, structures] of [['function', result.functions ?? []], ['class', result.classes ?? []]]) {
    for (const structure of structures) {
      const key = `${batchFile.path}:${structure.name}`;
      const symbol = symbolMeta[key];
      if (!symbol) throw new Error(`Missing symbol metadata for ${key}`);
      const id = `${type}:${batchFile.path}:${structure.name}`;
      nodes.push({
        id,
        type,
        name: structure.name,
        filePath: batchFile.path,
        lineRange: [structure.startLine, structure.endLine],
        summary: symbol[0],
        tags: symbol[1],
        complexity: complexityForLines(structure.endLine - structure.startLine + 1),
      });
      edges.push({ source: `file:${batchFile.path}`, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
      if (exportNames.has(structure.name)) {
        edges.push({ source: `file:${batchFile.path}`, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
      }
    }
  }
}

let importEdgeCount = 0;
for (const batchFile of input.batchFiles) {
  for (const target of input.batchImportData[batchFile.path]) {
    edges.push({ source: `file:${batchFile.path}`, target: `file:${target}`, type: 'imports', direction: 'forward', weight: 0.7 });
    importEdgeCount += 1;
  }
}

const inherit = (sourcePath, sourceClass, targetPath, targetClass) => edges.push({
  source: `class:${sourcePath}:${sourceClass}`,
  target: `class:${targetPath}:${targetClass}`,
  type: 'inherits',
  direction: 'forward',
  weight: 0.9,
});

const basePath = 'backend/assumption_zero/llm/base.py';
inherit('backend/assumption_zero/llm/beta_adapter.py', 'BetaAdapter', 'backend/assumption_zero/llm/openrouter_adapter.py', 'OpenRouterAdapter');
for (const [adapterPath, adapterClass] of [
  ['backend/assumption_zero/llm/fallback_adapter.py', 'FallbackChainAdapter'],
  ['backend/assumption_zero/llm/groq_adapter.py', 'GroqAdapter'],
  ['backend/assumption_zero/llm/hybrid_adapter.py', 'HybridLLMAdapter'],
  ['backend/assumption_zero/llm/mock_adapter.py', 'MockAdapter'],
  ['backend/assumption_zero/llm/ollama_adapter.py', 'OllamaAdapter'],
  ['backend/assumption_zero/llm/openai_compat_adapter.py', 'OpenAICompatAdapter'],
  ['backend/assumption_zero/llm/opencode_adapter.py', 'OpencodeAdapter'],
  ['backend/assumption_zero/llm/openrouter_adapter.py', 'OpenRouterAdapter'],
]) inherit(adapterPath, adapterClass, basePath, 'LLMAdapter');

const dependsOn = (sourcePath, sourceClass, targetPath, targetClass) => edges.push({
  source: `class:${sourcePath}:${sourceClass}`,
  target: `class:${targetPath}:${targetClass}`,
  type: 'depends_on',
  direction: 'forward',
  weight: 0.6,
});
dependsOn('backend/assumption_zero/llm/hybrid_adapter.py', 'HybridLLMAdapter', 'backend/assumption_zero/llm/groq_adapter.py', 'GroqAdapter');
dependsOn('backend/assumption_zero/llm/hybrid_adapter.py', 'HybridLLMAdapter', 'backend/assumption_zero/llm/openrouter_adapter.py', 'OpenRouterAdapter');
dependsOn('backend/assumption_zero/llm/fallback_adapter.py', 'FallbackChainAdapter', 'backend/assumption_zero/llm/mock_adapter.py', 'MockAdapter');

const call = (sourcePath, sourceName, targetType, targetPath, targetName) => edges.push({
  source: `function:${sourcePath}:${sourceName}`,
  target: `${targetType}:${targetPath}:${targetName}`,
  type: 'calls',
  direction: 'forward',
  weight: 0.8,
});
call('backend/assumption_zero/llm/openrouter_adapter.py', '_parse_output', 'function', 'backend/assumption_zero/llm/openrouter_adapter.py', '_repair_and_parse_json');
call('backend/tests/test_llm_adapters.py', 'test_build_all_llm_adapters', 'function', 'backend/assumption_zero/services/analysis_service.py', 'build_llm_adapter');
call('backend/tests/test_llm_adapters.py', 'test_explicit_provider_never_silently_falls_back_to_mock', 'function', 'backend/assumption_zero/services/analysis_service.py', 'build_llm_adapter');
call('backend/tests/test_llm_adapters.py', 'test_mock_adapter_parse_prompt', 'class', 'backend/assumption_zero/llm/mock_adapter.py', 'MockAdapter');
call('backend/tests/test_llm_adapters.py', 'test_gibberish_rejection_in_adapters', 'class', 'backend/assumption_zero/llm/mock_adapter.py', 'MockAdapter');
call('backend/tests/test_llm_adapters.py', 'test_fallback_chain_adapter', 'class', 'backend/assumption_zero/llm/mock_adapter.py', 'MockAdapter');
call('backend/tests/test_llm_adapters.py', 'test_fallback_chain_adapter', 'class', 'backend/assumption_zero/llm/fallback_adapter.py', 'FallbackChainAdapter');

for (const productionPath of [
  'backend/assumption_zero/llm/__init__.py',
  'backend/assumption_zero/llm/fallback_adapter.py',
  'backend/assumption_zero/llm/mock_adapter.py',
]) {
  edges.push({
    source: `file:${productionPath}`,
    target: 'file:backend/tests/test_llm_adapters.py',
    type: 'tested_by',
    direction: 'forward',
    weight: 0.5,
  });
}

const expectedImports = Object.values(input.batchImportData).reduce((sum, targets) => sum + targets.length, 0);
if (importEdgeCount !== expectedImports) throw new Error(`Import edge mismatch: ${importEdgeCount} != ${expectedImports}`);
if (new Set(nodes.map((node) => node.id)).size !== nodes.length) throw new Error('Duplicate node IDs');
if (edges.some((edge) => edge.source === edge.target)) throw new Error('Self-referencing edge');
if (nodes.length > 60 || edges.length > 120) throw new Error(`Unexpected split required: ${nodes.length} nodes, ${edges.length} edges`);

const localIds = new Set(nodes.map((node) => node.id));
const knownFiles = new Set([
  ...Object.keys(input.batchImportData),
  ...Object.values(input.batchImportData).flat(),
].map((item) => `file:${item}`));
const neighborSymbols = new Set();
for (const neighbors of Object.values(batch.neighborMap ?? {})) {
  for (const neighbor of neighbors) {
    for (const symbol of neighbor.symbols ?? []) {
      neighborSymbols.add(`function:${neighbor.path}:${symbol}`);
      neighborSymbols.add(`class:${neighbor.path}:${symbol}`);
    }
  }
}
for (const edge of edges) {
  for (const endpoint of [edge.source, edge.target]) {
    if (!localIds.has(endpoint) && !knownFiles.has(endpoint) && !neighborSymbols.has(endpoint)) {
      throw new Error(`Unvalidated edge endpoint ${endpoint}`);
    }
  }
}

const outputPath = path.join(uaDir, 'intermediate/batch-4.json');
fs.writeFileSync(outputPath, `${JSON.stringify({ nodes, edges }, null, 2)}\n`, 'utf8');
const parsed = JSON.parse(fs.readFileSync(outputPath, 'utf8'));
if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) throw new Error('Invalid batch-4.json');
console.log(JSON.stringify({ outputPath, nodes: nodes.length, edges: edges.length, imports: importEdgeCount }, null, 2));
