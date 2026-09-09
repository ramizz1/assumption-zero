import fs from 'node:fs';
import path from 'node:path';

const root = 'C:/Users/user/Desktop/idea/assumption-zero';
const ua = path.join(root, '.ua');
const input = JSON.parse(fs.readFileSync(path.join(ua, 'tmp/ua-file-analyzer-input-2.json'), 'utf8'));
const extracted = JSON.parse(fs.readFileSync(path.join(ua, 'tmp/ua-file-extract-results-2.json'), 'utf8'));

const fileMeta = {
  'backend/assumption_zero/analysis/__init__.py': ['Public package barrel exposing the validation engine’s core analysis helpers and orchestration API.', ['entry-point', 'barrel', 'analysis', 'exports']],
  'backend/assumption_zero/analysis/citation_validator.py': ['Validates model-supplied evidence citations, preserving known evidence identifiers and moving unknown identifiers into each perspective’s invalid-citation list.', ['validation', 'citations', 'evidence', 'analysis']],
  'backend/assumption_zero/analysis/competitor_merger.py': ['Normalizes, compares, merges, and ranks competitor records so duplicate discoveries become a single evidence-rich competitor profile.', ['competitor-research', 'deduplication', 'normalization', 'analysis']],
  'backend/assumption_zero/analysis/confidence.py': ['Calculates evidence-confidence levels from source volume, diversity, reliability, recency, and citation validity across model perspectives.', ['confidence-scoring', 'evidence', 'citations', 'analysis']],
  'backend/assumption_zero/analysis/disagreement.py': ['Detects recommendation, dimension-score, and assumption disagreements between model perspectives and records the competing positions for review.', ['multi-model', 'disagreement-detection', 'analysis', 'validation']],
  'backend/assumption_zero/analysis/engine.py': ['Orchestrates the complete validation pipeline: research collection, parallel model perspectives, grounded competitor extraction, scoring, confidence, regional analysis, experiments, and founder guidance.', ['service', 'orchestration', 'analysis-engine', 'research-pipeline', 'entry-point']],
  'backend/assumption_zero/analysis/experiment_generator.py': ['Selects prioritized validation experiments from reusable templates based on the idea, evidence, and model perspectives.', ['experiment-generation', 'validation', 'recommendation', 'analysis']],
  'backend/assumption_zero/analysis/founder_toolkit.py': ['Transforms analysis outcomes into a founder-facing toolkit with positioning, channels, metrics, interview prompts, decision rules, and a phased action roadmap.', ['founder-toolkit', 'roadmap', 'recommendation', 'analysis']],
  'backend/assumption_zero/analysis/query_generator.py': ['Generates categorized market, competitor, pricing, regional, regulatory, and validation research queries from structured idea details.', ['query-generation', 'research', 'market-analysis', 'utility']],
  'backend/assumption_zero/analysis/regional_analysis.py': ['Filters evidence for geography-specific signals and produces regional demand, pricing, regulatory, distribution, localization, and research-gap assessments.', ['regional-analysis', 'market-research', 'evidence', 'scoring']],
  'backend/assumption_zero/analysis/scoring.py': ['Aggregates model dimension scores into a weighted opportunity score with evidence links, confidence, explanations, and missing-information notes.', ['opportunity-scoring', 'evidence', 'aggregation', 'analysis']],
  'backend/assumption_zero/demo.py': ['Provides deterministic demo analysis data for product previews and local demonstrations without external research or model calls.', ['demo', 'sample-data', 'development', 'utility']],
  'backend/assumption_zero/research/demo_provider.py': ['Implements a deterministic research provider that returns bundled demo evidence while conforming to the standard research-provider interface.', ['research-provider', 'demo', 'service', 'test-double']],
  'backend/assumption_zero/schemas.py': ['Defines the project’s enums and Pydantic models for ideas, evidence, competitors, perspectives, scores, experiments, regional analysis, API requests, and analysis results, including input validation.', ['data-model', 'type-definition', 'validation', 'pydantic', 'schema-definition']],
  'backend/tests/conftest.py': ['Defines reusable pytest fixtures for isolated storage, sample ideas, evidence, and multi-model perspectives used throughout backend tests.', ['test', 'fixtures', 'pytest', 'sample-data']],
  'backend/tests/test_citations.py': ['Verifies that citation validation preserves valid evidence IDs, rejects unknown IDs, and handles empty evidence and citation lists.', ['test', 'citations', 'validation', 'pytest']],
  'backend/tests/test_competitors.py': ['Tests competitor normalization and merging plus evidence-grounding rules for AI-discovered and user-supplied competitors.', ['test', 'competitor-research', 'evidence-grounding', 'pytest']],
  'backend/tests/test_confidence.py': ['Tests evidence-confidence behavior across empty, sparse, and high-quality evidence sets and confirms independence from opportunity scores.', ['test', 'confidence-scoring', 'evidence', 'pytest']],
  'backend/tests/test_engine_e2e.py': ['Exercises the analysis engine end to end with deterministic adapter and research-provider doubles, including grounded competitor survival through the full pipeline.', ['test', 'end-to-end', 'analysis-engine', 'test-doubles']],
  'backend/tests/test_founder_toolkit.py': ['Verifies that generated founder toolkits contain measurable roadmaps and honor the acquisition channels declared in the idea.', ['test', 'founder-toolkit', 'roadmap', 'pytest']],
  'backend/tests/test_regional_research.py': ['Tests regional evidence filtering, research-depth controls, perspective volume, and fallback parsing of user-supplied competitor and geography details.', ['test', 'regional-analysis', 'research-depth', 'pytest']],
  'backend/tests/test_scoring.py': ['Validates scoring weights, dimension coverage, determinism, bounds, weighted totals, and extreme or missing-perspective behavior.', ['test', 'opportunity-scoring', 'aggregation', 'pytest']]
};

const action = (name) => name
  .replace(/^test_/, '')
  .replace(/^_/, '')
  .replaceAll('_', ' ')
  .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
  .toLowerCase();
const functionSummary = (file, name) => {
  if (name.startsWith('test_')) return `Verifies that ${action(name)}.`;
  const exact = {
    validate_citations: 'Reconciles cited evidence identifiers in model perspectives against the collected evidence set.',
    merge_competitors: 'Deduplicates and ranks competitor profiles while preserving the strongest combined evidence and attributes.',
    calculate_evidence_confidence: 'Computes an evidence-confidence level from quantity, diversity, reliability, recency, and citation coverage.',
    detect_disagreements: 'Compares model perspectives and emits structured disagreements for conflicting recommendations, scores, and assumptions.',
    generate_experiments: 'Returns prioritized validation experiments tailored to the idea and current evidence.',
    generate_founder_toolkit: 'Builds actionable positioning, channel, metric, interview, and roadmap guidance for the founder.',
    generate_queries: 'Creates categorized research queries from the idea’s market, customer, geography, and competitor context.',
    generate_regional_analysis: 'Produces geography-specific market scores, signals, localization needs, and evidence gaps.',
    calculate_opportunity_score: 'Calculates the weighted seven-dimension opportunity score and supporting evidence explanations.',
    is_gibberish: 'Applies lexical and character-distribution heuristics to reject empty or nonsensical user input.',
    isolated_storage: 'Temporarily redirects persistence paths so each test runs against isolated storage.',
    sample_idea: 'Creates a representative structured startup idea for tests.',
    sample_evidence: 'Creates representative supporting and contradicting evidence records for tests.',
    sample_perspectives: 'Creates deterministic multi-model perspective fixtures tied to sample evidence.'
  };
  if (exact[name]) return exact[name];
  if (name.startsWith('_')) return `Supports ${action(name)} as an internal step in ${fileMeta[file][0].split('.')[0].toLowerCase()}.`;
  return `Implements ${action(name)} for ${fileMeta[file][0].split('.')[0].toLowerCase()}.`;
};

const classSummary = (file, name) => {
  const exact = {
    AnalysisEngine: 'Coordinates research providers and model adapters through the full evidence-backed idea-validation workflow.',
    DemoProvider: 'Research-provider implementation that serves deterministic bundled evidence for demo runs.',
    MockAdapter: 'Deterministic model-adapter test double used to exercise the engine without an external LLM.',
    MockProvider: 'Research-provider test double that returns predictable evidence to engine tests.',
    CompetitorProvider: 'Test research provider that emits evidence naming a competitor.',
    CompetitorAIAdapter: 'Test model adapter that augments deterministic perspective output with an AI-discovered competitor.'
  };
  if (exact[name]) return exact[name];
  const enums = new Set(['EvidenceType', 'ReliabilityLevel', 'ConfidenceLevel', 'AnalysisStatus', 'ResearchDepth', 'AnalysisStage', 'Recommendation', 'PerspectiveName', 'CompetitorType']);
  if (enums.has(name)) return `Enumerates the supported ${action(name)} values used across validation models and API payloads.`;
  return `Pydantic data model representing ${action(name)} within the validation engine’s typed contracts.`;
};

const complexity = (lines) => lines > 200 ? 'complex' : lines >= 50 ? 'moderate' : 'simple';
const nodes = [];
const edges = [];

for (const result of extracted.results) {
  const file = result.path;
  const fileId = `file:${file}`;
  const [summary, tags] = fileMeta[file];
  const fileNode = {
    id: fileId,
    type: 'file',
    name: path.posix.basename(file),
    filePath: file,
    summary,
    tags,
    complexity: complexity(result.nonEmptyLines)
  };
  if (file.endsWith('schemas.py')) fileNode.languageNotes = 'Uses Pydantic field validators and model validators to enforce input quality and provider constraints at API boundaries.';
  if (file.endsWith('engine.py')) fileNode.languageNotes = 'Uses asynchronous provider/model orchestration with defensive error isolation around external integrations.';
  nodes.push(fileNode);

  const exported = new Set((result.exports ?? []).map((item) => item.name));
  for (const fn of result.functions ?? []) {
    const length = fn.endLine - fn.startLine + 1;
    if (length < 10 && !exported.has(fn.name)) continue;
    const id = `function:${file}:${fn.name}`;
    nodes.push({
      id,
      type: 'function',
      name: fn.name,
      filePath: file,
      lineRange: [fn.startLine, fn.endLine],
      summary: functionSummary(file, fn.name),
      tags: file.includes('/tests/') ? ['test', 'pytest', 'validation'] : ['analysis', 'function', fn.name.startsWith('_') ? 'internal-helper' : 'public-api'],
      complexity: complexity(length)
    });
    edges.push({ source: fileId, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
    if (exported.has(fn.name)) edges.push({ source: fileId, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
  }

  for (const cls of result.classes ?? []) {
    const length = cls.endLine - cls.startLine + 1;
    if ((cls.methods?.length ?? 0) < 2 && length < 20 && !exported.has(cls.name)) continue;
    const id = `class:${file}:${cls.name}`;
    const testDouble = file.includes('/tests/') && !cls.name.startsWith('Test');
    nodes.push({
      id,
      type: 'class',
      name: cls.name,
      filePath: file,
      lineRange: [cls.startLine, cls.endLine],
      summary: classSummary(file, cls.name),
      tags: testDouble ? ['test', 'test-double', 'class'] : file.endsWith('schemas.py') ? ['data-model', 'pydantic', 'type-definition'] : ['service', 'orchestration', 'class'],
      complexity: complexity(length)
    });
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
    if (!partIds.has(edge.target) && !allowedFileTargets.has(edge.target)) {
      throw new Error(`Part ${index + 1} has invalid target ${edge.target}`);
    }
  }
  const output = { nodes: partNodes, edges: partEdges };
  fs.writeFileSync(path.join(ua, `intermediate/batch-2-part-${index + 1}.json`), `${JSON.stringify(output, null, 2)}\n`);
}

process.stdout.write(JSON.stringify({ parts, nodeCount, edgeCount, expectedImports, actualImports, filesSkipped: extracted.filesSkipped ?? [] }));
