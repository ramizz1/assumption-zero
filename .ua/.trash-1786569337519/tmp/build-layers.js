const fs = require('node:fs');
const path = require('node:path');

const projectRoot = 'C:/Users/user/Desktop/idea/assumption-zero';
const input = JSON.parse(fs.readFileSync(path.join(projectRoot, '.ua/tmp/ua-arch-input.json'), 'utf8'));

const layerSpecs = [
  {
    id: 'layer:frontend-ui',
    name: 'Frontend UI',
    description: 'React pages, reusable result components, application bootstrapping, and the responsive visual system for idea intake and evidence-backed reports.',
  },
  {
    id: 'layer:frontend-client',
    name: 'Frontend Client and Shared Logic',
    description: 'Typed API access, analysis polling, readiness checks, report serialization, presentation utilities, and browser-side domain contracts.',
  },
  {
    id: 'layer:api-application',
    name: 'API and Application Layer',
    description: 'FastAPI and CLI entry points plus application services that construct providers, run analyses, and expose the persisted analysis lifecycle.',
  },
  {
    id: 'layer:analysis-engine',
    name: 'Analysis Engine',
    description: 'Core validation logic for orchestration, citation grounding, competitor consolidation, confidence, disagreements, scoring, regional conclusions, experiments, and founder actions.',
  },
  {
    id: 'layer:research',
    name: 'Evidence Research Layer',
    description: 'Research-provider abstractions and source integrations that collect and normalize web, community, repository, news, academic, and reference evidence.',
  },
  {
    id: 'layer:llm-integration',
    name: 'LLM Integration Layer',
    description: 'Shared model contracts, evidence-aware prompting, deterministic analysis, provider adapters, model routing, and resilient failover across local and hosted AI services.',
  },
  {
    id: 'layer:data-contracts',
    name: 'Data Contracts and Persistence',
    description: 'Validated domain schemas, database and file-storage models, demo fixtures, and the canonical example input used across the validation engine.',
  },
  {
    id: 'layer:test',
    name: 'Test Layer',
    description: 'Pytest and Vitest suites that verify API, CLI, analysis, research, model-adapter, UI, validation, scoring, export, and security behavior.',
  },
  {
    id: 'layer:infrastructure-config',
    name: 'Infrastructure and Configuration',
    description: 'Container topology, CI, development launchers, environment settings, package manifests, build tools, repository templates, and knowledge-graph configuration.',
  },
  {
    id: 'layer:documentation',
    name: 'Documentation',
    description: 'Project, backend, validation, security, contribution, and pull-request guidance for users, operators, and contributors.',
  },
];

const layers = layerSpecs.map((layer) => ({ ...layer, nodeIds: [] }));
const layerById = new Map(layers.map((layer) => [layer.id, layer]));
const add = (layerId, node) => layerById.get(layerId).nodeIds.push(node.id);

for (const node of input.fileNodes) {
  const p = node.filePath.replaceAll('\\', '/');
  if (node.type === 'document') {
    add('layer:documentation', node);
  } else if (p.startsWith('backend/tests/') || p.startsWith('frontend/tests/')) {
    add('layer:test', node);
  } else if (
    p === 'frontend/index.html' ||
    p === 'frontend/src/App.tsx' ||
    p === 'frontend/src/index.css' ||
    p === 'frontend/src/main.tsx' ||
    p.startsWith('frontend/src/components/') ||
    p.startsWith('frontend/src/pages/')
  ) {
    add('layer:frontend-ui', node);
  } else if (
    p.startsWith('frontend/src/hooks/') ||
    p.startsWith('frontend/src/lib/') ||
    p.startsWith('frontend/src/types/')
  ) {
    add('layer:frontend-client', node);
  } else if (p.startsWith('backend/assumption_zero/analysis/')) {
    add('layer:analysis-engine', node);
  } else if (p.startsWith('backend/assumption_zero/research/')) {
    add('layer:research', node);
  } else if (p.startsWith('backend/assumption_zero/llm/')) {
    add('layer:llm-integration', node);
  } else if ([
    'backend/assumption_zero/demo.py',
    'backend/assumption_zero/models.py',
    'backend/assumption_zero/schemas.py',
    'backend/assumption_zero/storage.py',
    'examples/sample-idea.json',
  ].includes(p)) {
    add('layer:data-contracts', node);
  } else if (
    p === 'backend/assumption_zero/__init__.py' ||
    p === 'backend/assumption_zero/cli.py' ||
    p === 'backend/assumption_zero/main.py' ||
    p.startsWith('backend/assumption_zero/api/') ||
    p.startsWith('backend/assumption_zero/services/')
  ) {
    add('layer:api-application', node);
  } else {
    add('layer:infrastructure-config', node);
  }
}

for (const layer of layers) layer.nodeIds.sort();
if (layers.length < 3 || layers.length > 10) throw new Error(`Invalid layer count ${layers.length}`);
if (layers.some((layer) => layer.nodeIds.length === 0)) throw new Error('Empty architecture layer');
const assigned = layers.flatMap((layer) => layer.nodeIds);
if (assigned.length !== input.fileNodes.length) throw new Error(`Assignment count mismatch: ${assigned.length} != ${input.fileNodes.length}`);
if (new Set(assigned).size !== assigned.length) throw new Error('Duplicate layer membership');
const inputIds = new Set(input.fileNodes.map((node) => node.id));
const unknown = assigned.filter((id) => !inputIds.has(id));
const missing = [...inputIds].filter((id) => !assigned.includes(id));
if (unknown.length || missing.length) throw new Error(`Coverage failure: unknown=${unknown.length}, missing=${missing.length}`);

const outputPath = path.join(projectRoot, '.ua/intermediate/layers.json');
fs.writeFileSync(outputPath, `${JSON.stringify(layers, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ total: assigned.length, layers: layers.map((layer) => ({ id: layer.id, count: layer.nodeIds.length })) }, null, 2));
