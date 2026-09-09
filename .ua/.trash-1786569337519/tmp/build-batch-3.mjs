import fs from 'node:fs';
import path from 'node:path';

const root = 'C:/Users/user/Desktop/idea/assumption-zero';
const ua = path.join(root, '.ua');
const input = JSON.parse(fs.readFileSync(path.join(ua, 'tmp/ua-file-analyzer-input-3.json'), 'utf8'));
const extracted = JSON.parse(fs.readFileSync(path.join(ua, 'tmp/ua-file-extract-results-3.json'), 'utf8'));

const fileMeta = {
  'backend/assumption_zero/api/routes.py': ['Defines the FastAPI HTTP surface for health checks, credential verification, idea and prompt analysis creation, history retrieval, deletion, and demo execution.', ['api-handler', 'fastapi', 'routing', 'analysis-service', 'entry-point']],
  'backend/assumption_zero/config.py': ['Defines environment-backed application settings, validates provider and URL configuration, masks secrets, and exposes a cached settings instance.', ['configuration', 'validation', 'security', 'settings', 'pydantic']],
  'backend/assumption_zero/models.py': ['Defines SQLAlchemy persistence models plus cached synchronous and asynchronous engines, session factories, and database initialization helpers.', ['data-model', 'database', 'sqlalchemy', 'persistence']],
  'backend/assumption_zero/research/__init__.py': ['Public package barrel exposing the research-provider abstraction and all bundled evidence-source implementations.', ['entry-point', 'barrel', 'research', 'exports']],
  'backend/assumption_zero/research/arxiv_provider.py': ['Implements an arXiv research provider that searches academic papers and converts results into normalized evidence records.', ['research-provider', 'academic-research', 'evidence', 'service']],
  'backend/assumption_zero/research/base.py': ['Defines the abstract asynchronous contract and shared text-truncation behavior implemented by all research providers.', ['research-provider', 'interface', 'abstraction', 'service']],
  'backend/assumption_zero/research/github_provider.py': ['Implements GitHub repository search and maps repository metadata into normalized competitor and validation evidence.', ['research-provider', 'github', 'competitor-research', 'service']],
  'backend/assumption_zero/research/hackernews_provider.py': ['Implements Hacker News search and classifies stories into evidence types for demand, pain, competitor, and market validation.', ['research-provider', 'hacker-news', 'market-research', 'service']],
  'backend/assumption_zero/research/news_provider.py': ['Implements news search through the configured SearXNG endpoint and converts recent articles into normalized evidence.', ['research-provider', 'news-search', 'evidence', 'service']],
  'backend/assumption_zero/research/reddit_provider.py': ['Implements Reddit search with query-type classification, relevance scoring, and normalized community evidence extraction.', ['research-provider', 'reddit', 'customer-research', 'service']],
  'backend/assumption_zero/research/searxng_provider.py': ['Implements general web research through SearXNG with source-domain reliability assessment and normalized evidence mapping.', ['research-provider', 'searxng', 'web-search', 'reliability']],
  'backend/assumption_zero/research/web_search_provider.py': ['Implements a lightweight web-search provider that classifies search results by query intent and emits normalized evidence records.', ['research-provider', 'web-search', 'evidence', 'service']],
  'backend/assumption_zero/research/wikipedia_provider.py': ['Implements Wikipedia title search and summary retrieval for background, market, competitor, and regulatory evidence.', ['research-provider', 'wikipedia', 'background-research', 'service']],
  'backend/assumption_zero/services/analysis_service.py': ['Provides the application service layer for adapter and research-provider construction, analysis lifecycle orchestration, persistence, history filtering, and deletion.', ['service', 'analysis-lifecycle', 'factory', 'persistence', 'orchestration']]
};

const phrase = (name) => name
  .replace(/^_/, '')
  .replaceAll('_', ' ')
  .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
  .toLowerCase();

const functionSummary = (file, name) => {
  const exact = {
    _available_providers: 'Returns availability information for every configured AI and research provider.',
    _llm_options: 'Normalizes the selected provider’s API key, model, and base-URL overrides from an API request.',
    _validate_selected_provider: 'Rejects requests that select unsupported or unavailable AI providers.',
    health: 'Returns application health, version, provider availability, and demo-mode status.',
    verify_keys_endpoint: 'Checks supplied provider credentials and endpoints, returning per-provider verification results without persisting secrets.',
    create_analysis_endpoint: 'Creates an analysis record from structured idea input and schedules background execution.',
    create_analysis_from_prompt_endpoint: 'Parses a free-form founder prompt into structured idea input, creates the record, and schedules analysis.',
    list_analyses_endpoint: 'Returns filtered and limited analysis-history summaries.',
    get_analysis_endpoint: 'Returns a stored analysis result by identifier.',
    delete_analysis_endpoint: 'Deletes a stored analysis result by identifier.',
    demo_endpoint: 'Creates and schedules a deterministic demo analysis using bundled idea data.',
    is_public_http_url: 'Validates that a configured HTTP URL is public and rejects local, private, or non-HTTP destinations to reduce SSRF risk.',
    get_settings: 'Returns the process-wide cached application settings object.',
    get_sync_engine: 'Lazily constructs and caches the synchronous SQLAlchemy engine.',
    get_sync_session: 'Returns the cached synchronous SQLAlchemy session factory.',
    get_async_engine: 'Lazily constructs and caches the asynchronous SQLAlchemy engine.',
    get_async_session_maker: 'Returns the cached asynchronous SQLAlchemy session factory.',
    init_db: 'Creates the configured database tables through the SQLAlchemy metadata.',
    _stable_id: 'Creates a deterministic evidence identifier from a source URL.',
    _ev_type: 'Maps research query intent to the corresponding evidence type.',
    _ev_type_for_hn: 'Classifies Hacker News results into evidence types from their title and query intent.',
    _ev_type_for_wiki: 'Maps Wikipedia query intent to the corresponding evidence type.',
    _reliability_from_domain: 'Assigns source reliability from the result URL’s domain characteristics.',
    build_llm_adapter: 'Constructs the requested model adapter, including provider-specific credentials, models, endpoints, and fallback behavior.',
    build_research_providers: 'Constructs the enabled research-provider set from configuration and request overrides.',
    create_analysis: 'Creates and persists an initial analysis record before background processing starts.',
    run_analysis: 'Builds integrations, runs the analysis engine with progress persistence, and stores either the completed result or failure state.',
    get_analysis: 'Loads and reconstructs a complete stored analysis result by identifier.',
    list_analyses: 'Queries analysis records with search, status, verdict, and limit filters and maps them to API list items.',
    delete_analysis: 'Deletes the specified analysis record from persistence.',
    _parse_dt: 'Parses an optional persisted datetime string into a datetime value.'
  };
  return exact[name] ?? `Implements ${phrase(name)} for ${fileMeta[file][0].split('.')[0].toLowerCase()}.`;
};

const classSummary = (name) => ({
  Settings: 'Environment-backed settings model with provider validation, safe URL checks, secret masking, and runtime limits.',
  Base: 'Declarative SQLAlchemy base shared by persistent application models.',
  AnalysisRecord: 'Persistent database record storing analysis lifecycle state, serialized input/result payloads, scores, recommendations, and timestamps.',
  ResearchProvider: 'Abstract asynchronous interface defining provider identity, availability, search, and shared passage truncation.',
  ArxivProvider: 'Research-provider implementation for academic-paper evidence from arXiv.',
  GitHubProvider: 'Research-provider implementation for repository and developer-ecosystem evidence from GitHub.',
  HackerNewsProvider: 'Research-provider implementation for founder, launch, demand, and market signals from Hacker News.',
  NewsSearchProvider: 'Research-provider implementation for recent news evidence returned through SearXNG.',
  RedditProvider: 'Research-provider implementation for pain points, demand, alternatives, and sentiment from Reddit communities.',
  SearXNGProvider: 'General web research provider backed by SearXNG with domain-based reliability classification.',
  WebSearchProvider: 'General search-result provider that maps query intent into normalized evidence records.',
  WikipediaProvider: 'Background research provider that resolves Wikipedia titles and summaries into normalized evidence.'
}[name] ?? `Implements the ${phrase(name)} class.`);

const complexity = (lines) => lines > 200 ? 'complex' : lines >= 50 ? 'moderate' : 'simple';
const nodes = [];
const edges = [];

for (const result of extracted.results) {
  const file = result.path;
  const fileId = `file:${file}`;
  const [summary, tags] = fileMeta[file];
  const fileNode = { id: fileId, type: 'file', name: path.posix.basename(file), filePath: file, summary, tags, complexity: complexity(result.nonEmptyLines) };
  if (file.endsWith('config.py')) fileNode.languageNotes = 'Uses Pydantic Settings with cached construction and explicit public-URL validation for configurable network endpoints.';
  if (file.includes('/research/') && !file.endsWith('__init__.py')) fileNode.languageNotes = 'Uses asynchronous HTTP access and maps heterogeneous source responses into the shared EvidenceItem schema.';
  if (file.endsWith('analysis_service.py')) fileNode.languageNotes = 'Centralizes asynchronous orchestration while persisting stage progress and final typed results through SQLAlchemy-backed storage.';
  nodes.push(fileNode);

  const exported = new Set((result.exports ?? []).map((item) => item.name));
  for (const fn of result.functions ?? []) {
    const length = fn.endLine - fn.startLine + 1;
    if (length < 10 && !exported.has(fn.name)) continue;
    const id = `function:${file}:${fn.name}`;
    const routeHandler = file.endsWith('routes.py') && !fn.name.startsWith('_');
    nodes.push({ id, type: 'function', name: fn.name, filePath: file, lineRange: [fn.startLine, fn.endLine], summary: functionSummary(file, fn.name), tags: routeHandler ? ['api-handler', 'fastapi', 'endpoint'] : file.includes('/research/') ? ['research', 'evidence', 'utility'] : file.endsWith('analysis_service.py') ? ['service', 'analysis-lifecycle', 'persistence'] : ['utility', 'configuration', 'database'], complexity: complexity(length) });
    edges.push({ source: fileId, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
    if (exported.has(fn.name)) edges.push({ source: fileId, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
  }

  for (const cls of result.classes ?? []) {
    const length = cls.endLine - cls.startLine + 1;
    if ((cls.methods?.length ?? 0) < 2 && length < 20 && !exported.has(cls.name)) continue;
    const id = `class:${file}:${cls.name}`;
    nodes.push({ id, type: 'class', name: cls.name, filePath: file, lineRange: [cls.startLine, cls.endLine], summary: classSummary(cls.name), tags: file.includes('/research/') ? ['research-provider', 'service', 'evidence'] : file.endsWith('models.py') ? ['data-model', 'sqlalchemy', 'persistence'] : ['configuration', 'validation', 'pydantic'], complexity: complexity(length) });
    edges.push({ source: fileId, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
    if (exported.has(cls.name)) edges.push({ source: fileId, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
  }

  for (const target of input.batchImportData[file] ?? []) {
    edges.push({ source: fileId, target: `file:${target}`, type: 'imports', direction: 'forward', weight: 0.7 });
  }
}

const expectedImports = Object.values(input.batchImportData).reduce((total, imports) => total + imports.length, 0);
const actualImports = edges.filter((edge) => edge.type === 'imports').length;
if (actualImports !== expectedImports) throw new Error(`Import edge mismatch: expected ${expectedImports}, got ${actualImports}`);

const nodeCount = nodes.length;
const edgeCount = edges.length;
const parts = Math.ceil(Math.max(nodeCount / 60, edgeCount / 120));
const files = [...input.batchFiles].sort((a, b) => a.path.localeCompare(b.path)).map((entry) => entry.path);
const groupSize = Math.ceil(files.length / parts);
const allowedFileTargets = new Set(Object.values(input.batchImportData).flat().map((file) => `file:${file}`));

for (let index = 0; index < parts; index += 1) {
  const group = new Set(files.slice(index * groupSize, (index + 1) * groupSize));
  const partNodes = nodes.filter((node) => group.has(node.filePath));
  const partIds = new Set(partNodes.map((node) => node.id));
  const partEdges = edges.filter((edge) => partIds.has(edge.source));
  for (const edge of partEdges) {
    if (!partIds.has(edge.source)) throw new Error(`Part ${index + 1} has unknown source ${edge.source}`);
    if (!partIds.has(edge.target) && !allowedFileTargets.has(edge.target)) throw new Error(`Part ${index + 1} has invalid target ${edge.target}`);
  }
  fs.writeFileSync(path.join(ua, `intermediate/batch-3-part-${index + 1}.json`), `${JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2)}\n`);
}

process.stdout.write(JSON.stringify({ parts, nodeCount, edgeCount, expectedImports, actualImports, filesSkipped: extracted.filesSkipped ?? [] }));
