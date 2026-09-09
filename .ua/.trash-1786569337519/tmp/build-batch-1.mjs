import fs from 'node:fs';
import path from 'node:path';

const projectRoot = 'C:/Users/user/Desktop/idea/assumption-zero';
const uaDir = path.join(projectRoot, '.ua');
const input = JSON.parse(fs.readFileSync(path.join(uaDir, 'tmp/ua-file-analyzer-input-1.json'), 'utf8'));
const extraction = JSON.parse(fs.readFileSync(path.join(uaDir, 'tmp/ua-file-extract-results-1.json'), 'utf8'));

const fileMeta = {
  'frontend/src/App.tsx': ['Defines the top-level React router, directing the landing route to idea intake and analysis routes to the analysis workflow.', ['entry-point', 'component', 'routing']],
  'frontend/src/components/CitationBadge.tsx': ['Renders a compact evidence citation that resolves an evidence identifier and safely links to external source material.', ['component', 'evidence', 'security']],
  'frontend/src/components/CompetitorCard.tsx': ['Presents a competitor profile with pricing, positioning, strengths, weaknesses, complaints, differentiation, and supporting citations.', ['component', 'competitor-research', 'evidence']],
  'frontend/src/components/DisclaimerBanner.tsx': ['Displays the shared product disclaimer so research reports communicate the limits of automated analysis.', ['component', 'disclaimer', 'risk-communication']],
  'frontend/src/components/ExperimentCard.tsx': ['Visualizes a validation experiment with its hypothesis, method, audience, success criteria, cost, timing, and next decision.', ['component', 'experiment', 'validation']],
  'frontend/src/components/FinancialSimulator.tsx': ['Provides an interactive unit-economics simulator that derives customer acquisition, lifetime value, payback, break-even, and revenue projections from an idea.', ['component', 'financial-modeling', 'simulation']],
  'frontend/src/components/FounderToolkit.tsx': ['Renders an execution toolkit covering customer-discovery scripts, channels, metrics, roadmap actions, interviews, and decision rules.', ['component', 'founder-toolkit', 'validation']],
  'frontend/src/components/OpportunityGauge.tsx': ['Renders a score-driven circular opportunity gauge with normalized geometry, color semantics, and an accessible numeric value.', ['component', 'data-visualization', 'scoring']],
  'frontend/src/components/PerspectiveExplorer.tsx': ['Lets users switch among model perspectives and view each recommendation, score, and evidence-backed analysis panel.', ['component', 'multi-model', 'evidence']],
  'frontend/src/components/PerspectivePanel.tsx': ['Renders the detailed sections of one analytical perspective, including claims, evidence citations, recommendations, and discipline-specific iconography.', ['component', 'analysis', 'evidence']],
  'frontend/src/components/ProviderIcon.tsx': ['Maps supported AI provider identifiers to distinctive inline SVG marks for provider selection interfaces.', ['component', 'ai-provider', 'iconography']],
  'frontend/src/components/RegionalMarketPanel.tsx': ['Summarizes regional market attractiveness, launch stance, demand signals, risks, regulatory notes, channels, and localization guidance.', ['component', 'regional-analysis', 'market-research']],
  'frontend/src/components/SavedAnalysesModal.tsx': ['Loads and displays saved analyses in a modal, with navigation, deletion, recommendation styling, and empty or loading states.', ['component', 'saved-analyses', 'api-client']],
  'frontend/src/components/ScoreBreakdown.tsx': ['Explains the overall opportunity score through weighted sub-scores, confidence, and visual color cues.', ['component', 'scoring', 'data-visualization']],
  'frontend/src/components/SettingsModal.tsx': ['Provides persistent AI-provider configuration, credential fields, model selection, endpoint settings, connection testing, and provider-specific guidance.', ['component', 'configuration', 'ai-provider']],
  'frontend/src/hooks/useAnalysis.ts': ['Encapsulates analysis submission and polling state, exposing progress, result, error, and reset behavior to analysis pages.', ['hook', 'api-client', 'state-management']],
  'frontend/src/lib/api.ts': ['Implements the typed frontend API client, centralizing JSON requests, errors, analysis lifecycle calls, history management, and provider connection tests.', ['api-client', 'serialization', 'error-handling']],
  'frontend/src/lib/readiness.ts': ['Scores prompt and structured-form completeness, returning actionable warnings, suggestions, and a readiness level before analysis submission.', ['validation', 'scoring', 'utility']],
  'frontend/src/lib/report.ts': ['Serializes a completed analysis into a comprehensive Markdown report spanning verdict, scores, perspectives, markets, competitors, experiments, finances, toolkit, and evidence.', ['serialization', 'reporting', 'markdown']],
  'frontend/src/lib/utils.ts': ['Provides shared presentation helpers for score, recommendation, confidence, reliability, dates, safe URLs, progress stages, and the product disclaimer.', ['utility', 'formatting', 'security']],
  'frontend/src/main.tsx': ['Bootstraps the React application into the root DOM node, applying strict mode, browser routing, and global styles.', ['entry-point', 'react', 'routing']],
  'frontend/src/pages/AnalysisPage.tsx': ['Coordinates a single analysis run, starting work from navigation state and switching among error, progress, and completed-report views.', ['component', 'analysis-workflow', 'state-management']],
  'frontend/src/pages/HomePage.tsx': ['Implements the primary idea-intake experience, including raw-prompt and structured modes, provider and research-depth controls, readiness checks, file import, history, settings, and analysis launch.', ['component', 'idea-intake', 'analysis-workflow']],
  'frontend/src/pages/ProgressView.tsx': ['Visualizes the staged research and synthesis pipeline with progress percentages, active-state messaging, and completed-stage indicators.', ['component', 'progress-tracking', 'analysis-workflow']],
  'frontend/src/pages/ReportView.tsx': ['Orchestrates the full analysis report, loading results, filtering evidence, exporting Markdown or JSON, printing, and composing score, market, competitor, experiment, financial, and toolkit sections.', ['component', 'reporting', 'analysis-results']],
  'frontend/src/types/index.ts': ['Defines the frontend domain contracts for idea input, analysis state and results, evidence, competitors, markets, experiments, provider settings, scores, and toolkit output.', ['type-definition', 'domain-model', 'typescript']],
  'frontend/tests/citation.test.ts': ['Tests evidence lookup and URL classification behavior used by citation rendering and external-link safety.', ['test', 'evidence', 'url-validation']],
  'frontend/tests/perspectiveExplorer.test.tsx': ['Tests perspective selection and evidence presentation in the multi-model perspective explorer.', ['test', 'component', 'multi-model']],
  'frontend/tests/readiness.test.ts': ['Tests readiness scoring and guidance for both raw prompts and structured idea forms.', ['test', 'validation', 'scoring']],
  'frontend/tests/score.test.ts': ['Tests score and recommendation presentation utilities, confidence colors, safe URL handling, stage labels, and disclaimer content.', ['test', 'utility', 'scoring']],
};

const functionMeta = {
  'frontend/src/App.tsx:App': ['Creates the application route tree for intake and analysis pages.', ['component', 'routing', 'entry-point']],
  'frontend/src/components/CitationBadge.tsx:CitationBadge': ['Resolves and renders one evidence citation with safe link handling and source context.', ['component', 'evidence', 'security']],
  'frontend/src/components/CompetitorCard.tsx:CompetitorCard': ['Renders a detailed competitor research card and its supporting citations.', ['component', 'competitor-research', 'evidence']],
  'frontend/src/components/DisclaimerBanner.tsx:DisclaimerBanner': ['Renders the shared automated-analysis disclaimer banner.', ['component', 'disclaimer', 'risk-communication']],
  'frontend/src/components/ExperimentCard.tsx:ExperimentCard': ['Renders the plan, success criteria, and decision guidance for a validation experiment.', ['component', 'experiment', 'validation']],
  'frontend/src/components/FinancialSimulator.tsx:FinancialSimulator': ['Maintains adjustable unit-economics assumptions and calculates financial viability and projection data.', ['component', 'financial-modeling', 'simulation']],
  'frontend/src/components/FinancialSimulator.tsx:Slider': ['Renders a labeled range control used to tune simulator assumptions.', ['component', 'form-control', 'simulation']],
  'frontend/src/components/FounderToolkit.tsx:FounderToolkit': ['Renders an actionable founder playbook and supports copying its interview script.', ['component', 'founder-toolkit', 'clipboard']],
  'frontend/src/components/OpportunityGauge.tsx:OpportunityGauge': ['Draws a normalized circular opportunity score with semantic colors and labels.', ['component', 'data-visualization', 'scoring']],
  'frontend/src/components/PerspectiveExplorer.tsx:PerspectiveExplorer': ['Manages perspective selection and renders the active model analysis.', ['component', 'multi-model', 'state-management']],
  'frontend/src/components/PerspectivePanel.tsx:PerspectivePanel': ['Renders structured sections and citations for a single analytical perspective.', ['component', 'analysis', 'evidence']],
  'frontend/src/components/ProviderIcon.tsx:ProviderIcon': ['Selects and renders the SVG icon for an AI provider identifier.', ['component', 'ai-provider', 'iconography']],
  'frontend/src/components/RegionalMarketPanel.tsx:SignalList': ['Renders a labeled regional signal list with an empty-state fallback.', ['component', 'regional-analysis', 'list-rendering']],
  'frontend/src/components/RegionalMarketPanel.tsx:RegionalMarketPanel': ['Presents regional opportunity, risks, channels, regulations, and localization advice.', ['component', 'regional-analysis', 'market-research']],
  'frontend/src/components/SavedAnalysesModal.tsx:SavedAnalysesModal': ['Fetches, displays, opens, and deletes analysis-history entries inside a modal.', ['component', 'saved-analyses', 'api-client']],
  'frontend/src/components/ScoreBreakdown.tsx:ScoreBreakdown': ['Renders weighted score dimensions and confidence indicators for an analysis result.', ['component', 'scoring', 'data-visualization']],
  'frontend/src/components/SettingsModal.tsx:getStoredAISettings': ['Reads persisted provider settings and normalizes legacy or missing fields into defaults.', ['configuration', 'persistence', 'factory']],
  'frontend/src/components/SettingsModal.tsx:SettingsModal': ['Manages provider configuration, persistence, validation, and connection testing in a modal.', ['component', 'configuration', 'ai-provider']],
  'frontend/src/hooks/useAnalysis.ts:useAnalysis': ['Submits an idea for analysis and manages polling, progress, terminal results, errors, and reset state.', ['hook', 'api-client', 'state-management']],
  'frontend/src/lib/api.ts:request': ['Executes typed JSON requests and converts unsuccessful responses into useful client errors.', ['api-client', 'serialization', 'error-handling']],
  'frontend/src/lib/readiness.ts:assessPromptReadiness': ['Evaluates a free-form idea prompt for specificity, evidence, constraints, and research readiness.', ['validation', 'scoring', 'utility']],
  'frontend/src/lib/readiness.ts:assessFormReadiness': ['Evaluates structured idea fields and returns a readiness score with targeted corrective guidance.', ['validation', 'scoring', 'utility']],
  'frontend/src/lib/report.ts:generateMarkdownReport': ['Builds a downloadable Markdown representation of every major analysis result and evidence section.', ['serialization', 'reporting', 'markdown']],
  'frontend/src/lib/utils.ts:scoreColor': ['Maps an opportunity score to its semantic text color class.', ['utility', 'scoring', 'formatting']],
  'frontend/src/lib/utils.ts:scoreBgColor': ['Maps an opportunity score to its semantic background color class.', ['utility', 'scoring', 'formatting']],
  'frontend/src/lib/utils.ts:scoreBorderColor': ['Maps an opportunity score to its semantic border color class.', ['utility', 'scoring', 'formatting']],
  'frontend/src/lib/utils.ts:recommendationColor': ['Maps a recommendation label to its semantic text color class.', ['utility', 'recommendation', 'formatting']],
  'frontend/src/lib/utils.ts:recommendationBg': ['Maps a recommendation label to its semantic background color class.', ['utility', 'recommendation', 'formatting']],
  'frontend/src/lib/utils.ts:confidenceColor': ['Maps an evidence-confidence level to its semantic color class.', ['utility', 'confidence', 'formatting']],
  'frontend/src/lib/utils.ts:reliabilityBadge': ['Formats an evidence reliability rating as a compact badge label.', ['utility', 'evidence', 'formatting']],
  'frontend/src/lib/utils.ts:formatDate': ['Formats timestamps for concise human-readable display.', ['utility', 'date', 'formatting']],
  'frontend/src/lib/utils.ts:safeExternalUrl': ['Allows only safe external HTTP(S) URLs and rejects unsuitable link values.', ['utility', 'security', 'url-validation']],
  'frontend/src/lib/utils.ts:stageLabel': ['Converts analysis pipeline stage identifiers into readable labels.', ['utility', 'progress-tracking', 'formatting']],
  'frontend/src/pages/AnalysisPage.tsx:AnalysisPage': ['Starts or resumes analysis work and selects the appropriate error, progress, or report view.', ['component', 'analysis-workflow', 'state-management']],
  'frontend/src/pages/HomePage.tsx:ReadinessPanel': ['Displays readiness score, level, warnings, and suggestions beside idea inputs.', ['component', 'validation', 'scoring']],
  'frontend/src/pages/HomePage.tsx:HomePage': ['Manages idea intake, settings, research options, validation, file upload, and navigation into analysis.', ['component', 'idea-intake', 'analysis-workflow']],
  'frontend/src/pages/ProgressView.tsx:ProgressView': ['Renders current analysis stage, completion percentage, and the full staged workflow.', ['component', 'progress-tracking', 'analysis-workflow']],
  'frontend/src/pages/ReportView.tsx:ReportView': ['Loads and composes the complete evidence-backed report with filtering and export actions.', ['component', 'reporting', 'analysis-results']],
  'frontend/tests/perspectiveExplorer.test.tsx:perspective': ['Builds reusable perspective fixtures with optional field overrides for component tests.', ['test-fixture', 'factory', 'multi-model']],
};

const significant = new Set(Object.keys(functionMeta));
const resultByPath = new Map(extraction.results.map((item) => [item.path, item]));
const complexityForLines = (lines) => lines > 200 ? 'complex' : lines >= 50 ? 'moderate' : 'simple';
const nodes = [];
const edges = [];

for (const batchFile of input.batchFiles) {
  const result = resultByPath.get(batchFile.path);
  if (!result) throw new Error(`No extraction result for ${batchFile.path}`);
  const meta = fileMeta[batchFile.path];
  if (!meta) throw new Error(`No file metadata for ${batchFile.path}`);
  nodes.push({
    id: `file:${batchFile.path}`,
    type: 'file',
    name: path.posix.basename(batchFile.path),
    filePath: batchFile.path,
    summary: meta[0],
    tags: meta[1],
    complexity: complexityForLines(result.nonEmptyLines),
    ...(batchFile.path === 'frontend/src/types/index.ts' ? { languageNotes: 'Central TypeScript interface layer keeps the UI aligned with the backend analysis contract.' } : {}),
  });

  const exportNames = new Set((result.exports ?? []).map((item) => item.name));
  for (const fn of result.functions ?? []) {
    const key = `${batchFile.path}:${fn.name}`;
    if (!significant.has(key)) continue;
    const fnMeta = functionMeta[key];
    const id = `function:${batchFile.path}:${fn.name}`;
    nodes.push({
      id,
      type: 'function',
      name: fn.name,
      filePath: batchFile.path,
      lineRange: [fn.startLine, fn.endLine],
      summary: fnMeta[0],
      tags: fnMeta[1],
      complexity: complexityForLines(fn.endLine - fn.startLine + 1),
    });
    edges.push({ source: `file:${batchFile.path}`, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
    if (exportNames.has(fn.name)) {
      edges.push({ source: `file:${batchFile.path}`, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
    }
  }
}

let importEdgeCount = 0;
for (const batchFile of input.batchFiles) {
  for (const importedPath of input.batchImportData[batchFile.path]) {
    edges.push({ source: `file:${batchFile.path}`, target: `file:${importedPath}`, type: 'imports', direction: 'forward', weight: 0.7 });
    importEdgeCount += 1;
  }
}

const call = (sourcePath, sourceName, targetPath, targetName) => edges.push({
  source: `function:${sourcePath}:${sourceName}`,
  target: `function:${targetPath}:${targetName}`,
  type: 'calls',
  direction: 'forward',
  weight: 0.8,
});

call('frontend/src/pages/AnalysisPage.tsx', 'AnalysisPage', 'frontend/src/hooks/useAnalysis.ts', 'useAnalysis');
call('frontend/src/pages/HomePage.tsx', 'HomePage', 'frontend/src/lib/readiness.ts', 'assessPromptReadiness');
call('frontend/src/pages/HomePage.tsx', 'HomePage', 'frontend/src/lib/readiness.ts', 'assessFormReadiness');
call('frontend/src/pages/ProgressView.tsx', 'ProgressView', 'frontend/src/lib/utils.ts', 'stageLabel');
call('frontend/src/pages/ReportView.tsx', 'ReportView', 'frontend/src/lib/report.ts', 'generateMarkdownReport');
call('frontend/src/pages/ReportView.tsx', 'ReportView', 'frontend/src/lib/utils.ts', 'recommendationBg');
call('frontend/src/pages/ReportView.tsx', 'ReportView', 'frontend/src/lib/utils.ts', 'recommendationColor');
call('frontend/src/pages/ReportView.tsx', 'ReportView', 'frontend/src/lib/utils.ts', 'safeExternalUrl');

const testedBy = (production, test) => edges.push({
  source: `file:${production}`,
  target: `file:${test}`,
  type: 'tested_by',
  direction: 'forward',
  weight: 0.5,
});

testedBy('frontend/src/lib/utils.ts', 'frontend/tests/citation.test.ts');
testedBy('frontend/src/components/PerspectiveExplorer.tsx', 'frontend/tests/perspectiveExplorer.test.tsx');
testedBy('frontend/src/lib/readiness.ts', 'frontend/tests/readiness.test.ts');
testedBy('frontend/src/lib/utils.ts', 'frontend/tests/score.test.ts');

const expectedImports = Object.values(input.batchImportData).reduce((sum, values) => sum + values.length, 0);
if (importEdgeCount !== expectedImports) throw new Error(`Import edge mismatch: ${importEdgeCount} != ${expectedImports}`);
if (new Set(nodes.map((node) => node.id)).size !== nodes.length) throw new Error('Duplicate node IDs');
if (edges.some((edge) => edge.source === edge.target)) throw new Error('Self-referencing edge');

const nodeCount = nodes.length;
const edgeCount = edges.length;
const parts = Math.ceil(Math.max(nodeCount / 60, edgeCount / 120));
if (parts <= 1) throw new Error(`Expected split output, got ${nodeCount} nodes and ${edgeCount} edges`);

const sortedFiles = input.batchFiles.map((item) => item.path).sort((a, b) => a.localeCompare(b));
const groupSize = Math.ceil(sortedFiles.length / parts);
const allNodeIds = new Set(nodes.map((node) => node.id));
const allowedImportedFiles = new Set([
  ...Object.keys(input.batchImportData),
  ...Object.values(input.batchImportData).flat(),
].map((item) => `file:${item}`));
const outputs = [];

for (let index = 0; index < parts; index += 1) {
  const group = new Set(sortedFiles.slice(index * groupSize, (index + 1) * groupSize));
  const partNodes = nodes.filter((node) => group.has(node.filePath));
  const sourceIds = new Set(partNodes.map((node) => node.id));
  const partEdges = edges.filter((edge) => sourceIds.has(edge.source));
  for (const edge of partEdges) {
    if (!sourceIds.has(edge.source)) throw new Error(`Part ${index + 1} missing source ${edge.source}`);
    const targetInPart = sourceIds.has(edge.target);
    const verifiedImportedFile = allowedImportedFiles.has(edge.target);
    if (!targetInPart && !verifiedImportedFile) {
      throw new Error(`Part ${index + 1} has invalid external target ${edge.target}`);
    }
    if (!allNodeIds.has(edge.source)) throw new Error(`Unknown global source ${edge.source}`);
  }
  const output = { nodes: partNodes, edges: partEdges };
  const outputPath = path.join(uaDir, 'intermediate', `batch-1-part-${index + 1}.json`);
  fs.writeFileSync(outputPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
  outputs.push({ outputPath, nodes: partNodes.length, edges: partEdges.length });
}

for (const output of outputs) {
  const parsed = JSON.parse(fs.readFileSync(output.outputPath, 'utf8'));
  if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) throw new Error(`Invalid graph fragment ${output.outputPath}`);
}

console.log(JSON.stringify({ nodeCount, edgeCount, importEdgeCount, parts: outputs }, null, 2));
