const fs = require('node:fs');

function main() {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('Usage: node ua-tour-analyze.js <input> <output>');
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const { nodes, edges, layers } = input;
  if (!Array.isArray(nodes) || !Array.isArray(edges) || !Array.isArray(layers)) throw new Error('Invalid tour topology input');
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  if (nodeById.size !== nodes.length) throw new Error('Duplicate input node IDs');

  const fanIn = Object.fromEntries(nodes.map((node) => [node.id, 0]));
  const fanOut = Object.fromEntries(nodes.map((node) => [node.id, 0]));
  for (const edge of edges) {
    if (nodeById.has(edge.target)) fanIn[edge.target] += 1;
    if (nodeById.has(edge.source)) fanOut[edge.source] += 1;
  }
  const rank = (counts, key) => nodes
    .map((node) => ({ id: node.id, [key]: counts[node.id], name: node.name }))
    .sort((a, b) => b[key] - a[key] || a.id.localeCompare(b.id))
    .slice(0, 20);
  const fanInRanking = rank(fanIn, 'fanIn');
  const fanOutRanking = rank(fanOut, 'fanOut');
  const fanOutValues = nodes.map((node) => fanOut[node.id]).sort((a, b) => b - a);
  const highFanOutThreshold = fanOutValues[Math.max(0, Math.ceil(nodes.length * 0.1) - 1)] ?? 0;
  const fanInValues = nodes.map((node) => fanIn[node.id]).sort((a, b) => a - b);
  const lowFanInThreshold = fanInValues[Math.max(0, Math.ceil(nodes.length * 0.25) - 1)] ?? 0;
  const explicitEntries = new Set([
    'frontend/src/main.tsx',
    'frontend/src/App.tsx',
    'backend/assumption_zero/main.py',
    'backend/assumption_zero/cli.py',
    'backend/assumption_zero/api/routes.py',
  ]);
  const entryPattern = /^(index\.(ts|tsx|js|jsx)|main\.(ts|tsx|js|jsx|py|rs|go|cpp|c)|app\.(ts|tsx|js|jsx|py)|server\.(ts|tsx|js|jsx)|mod\.rs|manage\.py|wsgi\.py|asgi\.py|run\.py|__main__\.py|Application\.java|Main\.java|Program\.cs|config\.ru|index\.php|App\.swift|Application\.kt)$/i;
  const entryPointCandidates = nodes.map((node) => {
    const p = String(node.filePath ?? '').replaceAll('\\', '/');
    const depth = p.split('/').filter(Boolean).length;
    let score = 0;
    if (node.type === 'document' && p === 'README.md') score += 5;
    else if (node.type === 'document' && depth === 1 && /\.md$/i.test(p)) score += 2;
    if (node.type === 'file') {
      if (entryPattern.test(node.name) || explicitEntries.has(p)) score += 3;
      if (depth <= 2) score += 1;
      if (fanOut[node.id] >= highFanOutThreshold) score += 1;
      if (fanIn[node.id] <= lowFanInThreshold) score += 1;
    }
    return { id: node.id, score, name: node.name, summary: node.summary, type: node.type };
  }).filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || (a.type === 'document' ? -1 : 1) || a.id.localeCompare(b.id))
    .slice(0, 5);

  const codeStart = entryPointCandidates.find((item) => item.type === 'file');
  const adjacency = new Map(nodes.map((node) => [node.id, []]));
  for (const edge of edges) {
    if (!['imports', 'calls'].includes(edge.type)) continue;
    if (nodeById.has(edge.source) && nodeById.has(edge.target)) adjacency.get(edge.source).push(edge.target);
  }
  for (const targets of adjacency.values()) targets.sort();
  const order = [];
  const depthMap = {};
  const byDepth = {};
  if (codeStart) {
    const queue = [codeStart.id];
    depthMap[codeStart.id] = 0;
    while (queue.length) {
      const current = queue.shift();
      const depth = depthMap[current];
      order.push(current);
      (byDepth[depth] ??= []).push(current);
      for (const target of adjacency.get(current) ?? []) {
        if (depthMap[target] !== undefined) continue;
        depthMap[target] = depth + 1;
        queue.push(target);
      }
    }
  }

  const compact = (node) => ({ id: node.id, name: node.name, type: node.type, summary: node.summary });
  const nonCodeFiles = {
    documentation: nodes.filter((node) => node.type === 'document').map(compact),
    infrastructure: nodes.filter((node) => ['service', 'pipeline', 'resource'].includes(node.type)).map(compact),
    data: nodes.filter((node) => ['table', 'schema', 'endpoint'].includes(node.type)).map(compact),
    config: nodes.filter((node) => node.type === 'config').map(compact),
  };

  const relation = new Map();
  for (const edge of edges) {
    if (!['imports', 'calls'].includes(edge.type) || !nodeById.has(edge.source) || !nodeById.has(edge.target)) continue;
    relation.set(`${edge.source}\u0000${edge.target}`, (relation.get(`${edge.source}\u0000${edge.target}`) ?? 0) + 1);
  }
  const pairClusters = [];
  const seenPairs = new Set();
  for (const key of relation.keys()) {
    const [a, b] = key.split('\u0000');
    if (!relation.has(`${b}\u0000${a}`)) continue;
    const pairKey = [a, b].sort().join('\u0000');
    if (seenPairs.has(pairKey)) continue;
    seenPairs.add(pairKey);
    const members = new Set([a, b]);
    let expanded = true;
    while (expanded && members.size < 5) {
      expanded = false;
      for (const node of nodes) {
        if (members.has(node.id)) continue;
        let links = 0;
        for (const member of members) {
          if (relation.has(`${node.id}\u0000${member}`) || relation.has(`${member}\u0000${node.id}`)) links += 1;
        }
        if (links >= 2) {
          members.add(node.id);
          expanded = true;
          if (members.size >= 5) break;
        }
      }
    }
    let edgeCount = 0;
    for (const source of members) for (const target of members) edgeCount += relation.get(`${source}\u0000${target}`) ?? 0;
    pairClusters.push({ nodes: [...members].sort(), edgeCount });
  }
  const clusters = pairClusters.sort((a, b) => b.edgeCount - a.edgeCount || b.nodes.length - a.nodes.length).slice(0, 10);

  const nodeSummaryIndex = Object.fromEntries(nodes.map((node) => [node.id, { name: node.name, type: node.type, summary: node.summary }]));
  const result = {
    scriptCompleted: true,
    entryPointCandidates,
    fanInRanking,
    fanOutRanking,
    bfsTraversal: { startNode: codeStart?.id ?? null, order, depthMap, byDepth },
    nonCodeFiles,
    clusters,
    layers: { count: layers.length, list: layers },
    nodeSummaryIndex,
    totalNodes: nodes.length,
    totalEdges: edges.length,
  };
  fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
}

try {
  main();
} catch (error) {
  console.error(error?.stack ?? String(error));
  process.exit(1);
}
