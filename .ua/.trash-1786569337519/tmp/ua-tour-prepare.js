const fs = require('node:fs');
const path = require('node:path');

const root = 'C:/Users/user/Desktop/idea/assumption-zero';
const graph = JSON.parse(fs.readFileSync(path.join(root, '.ua/intermediate/assembled-graph.json'), 'utf8'));
const layers = JSON.parse(fs.readFileSync(path.join(root, '.ua/intermediate/layers.json'), 'utf8'));
const fileTypes = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);
const nodes = graph.nodes
  .filter((node) => fileTypes.has(node.type))
  .map(({ id, name, filePath, summary, type }) => ({ id, name, filePath, summary, type }));
const topologyLayers = layers.map(({ id, name, description }) => ({ id, name, description }));
const outputPath = path.join(root, '.ua/tmp/ua-tour-input.json');
fs.writeFileSync(outputPath, `${JSON.stringify({ nodes, edges: graph.edges, layers: topologyLayers }, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ outputPath, nodes: nodes.length, edges: graph.edges.length, layers: topologyLayers.length }));
