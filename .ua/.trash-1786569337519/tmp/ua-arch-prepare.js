const fs = require('node:fs');
const path = require('node:path');

const projectRoot = 'C:/Users/user/Desktop/idea/assumption-zero';
const graphPath = path.join(projectRoot, '.ua/intermediate/assembled-graph.json');
const outputPath = path.join(projectRoot, '.ua/tmp/ua-arch-input.json');
const graph = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
const fileTypes = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);
const fileNodes = graph.nodes
  .filter((node) => fileTypes.has(node.type))
  .map(({ id, type, name, filePath, summary, tags }) => ({ id, type, name, filePath, summary, tags }));
const fileIds = new Set(fileNodes.map((node) => node.id));
const importEdges = graph.edges.filter((edge) => edge.type === 'imports');
const nonFileImportEdges = importEdges.filter((edge) => !fileIds.has(edge.source) || !fileIds.has(edge.target));
if (nonFileImportEdges.length) throw new Error(`Found ${nonFileImportEdges.length} imports edges outside file-level nodes`);
const allEdges = graph.edges.filter((edge) => fileIds.has(edge.source) && fileIds.has(edge.target));
fs.writeFileSync(outputPath, `${JSON.stringify({ fileNodes, importEdges, allEdges }, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ outputPath, fileNodes: fileNodes.length, importEdges: importEdges.length, allEdges: allEdges.length }));
