const fs = require('node:fs');

function main() {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('Usage: node ua-arch-analyze.js <input> <output>');
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const { fileNodes, importEdges, allEdges } = input;
  if (!Array.isArray(fileNodes) || !Array.isArray(importEdges) || !Array.isArray(allEdges)) throw new Error('Invalid architecture input');

  const normalize = (value) => String(value ?? '').replaceAll('\\', '/');
  const segments = fileNodes.map((node) => normalize(node.filePath).split('/').filter(Boolean));
  let common = segments.length ? [...segments[0].slice(0, -1)] : [];
  for (const parts of segments.slice(1)) {
    const dirs = parts.slice(0, -1);
    let length = 0;
    while (length < common.length && length < dirs.length && common[length] === dirs[length]) length += 1;
    common = common.slice(0, length);
  }
  const flat = segments.every((parts) => parts.length <= common.length + 1);
  const classifyFlat = (node) => {
    const p = normalize(node.filePath).toLowerCase();
    if (/((^|\/)test_[^/]+|\.(test|spec)\.)/.test(p)) return 'test';
    if (node.type === 'document' || /\.(md|rst)$/.test(p)) return 'documentation';
    if (node.type === 'config' || /(^|\/)(package\.json|pyproject\.toml|tsconfig[^/]*\.json)$/.test(p)) return 'config';
    return p.includes('.') ? p.split('.').pop() : 'root';
  };
  const groupFor = (node) => {
    if (flat) return classifyFlat(node);
    const parts = normalize(node.filePath).split('/').filter(Boolean);
    return parts[common.length] && parts.length > common.length + 1 ? parts[common.length] : 'root';
  };

  const directoryGroups = {};
  const nodeTypeGroups = {};
  const groupById = new Map();
  const typeById = new Map();
  for (const node of fileNodes) {
    const group = groupFor(node);
    (directoryGroups[group] ??= []).push(node.id);
    (nodeTypeGroups[node.type] ??= []).push(node.id);
    groupById.set(node.id, group);
    typeById.set(node.id, node.type);
  }
  for (const value of Object.values(directoryGroups)) value.sort();
  for (const value of Object.values(nodeTypeGroups)) value.sort();

  const fileFanIn = Object.fromEntries(fileNodes.map((node) => [node.id, 0]));
  const fileFanOut = Object.fromEntries(fileNodes.map((node) => [node.id, 0]));
  const groupImports = Object.fromEntries(Object.keys(directoryGroups).map((group) => [group, { importsFrom: new Set(), importedBy: new Set() }]));
  const interCounts = new Map();
  for (const edge of importEdges) {
    fileFanOut[edge.source] += 1;
    fileFanIn[edge.target] += 1;
    const from = groupById.get(edge.source);
    const to = groupById.get(edge.target);
    if (!from || !to) throw new Error(`Import edge references unknown file node: ${edge.source} -> ${edge.target}`);
    if (from !== to) {
      groupImports[from].importsFrom.add(to);
      groupImports[to].importedBy.add(from);
    }
    const key = `${from}\u0000${to}`;
    interCounts.set(key, (interCounts.get(key) ?? 0) + 1);
  }

  const directoryAdjacency = {};
  for (const [group, data] of Object.entries(groupImports)) {
    directoryAdjacency[group] = {
      importsFrom: [...data.importsFrom].sort(),
      importedBy: [...data.importedBy].sort(),
    };
  }

  const crossCounts = new Map();
  for (const edge of allEdges) {
    const fromType = typeById.get(edge.source);
    const toType = typeById.get(edge.target);
    if (!fromType || !toType) throw new Error(`File-level edge references unknown node: ${edge.source} -> ${edge.target}`);
    if (fromType !== toType || edge.type !== 'imports') {
      const key = `${fromType}\u0000${toType}\u0000${edge.type}`;
      crossCounts.set(key, (crossCounts.get(key) ?? 0) + 1);
    }
  }
  const crossCategoryEdges = [...crossCounts.entries()].map(([key, count]) => {
    const [fromType, toType, edgeType] = key.split('\u0000');
    return { fromType, toType, edgeType, count };
  }).sort((a, b) => a.fromType.localeCompare(b.fromType) || a.toType.localeCompare(b.toType) || a.edgeType.localeCompare(b.edgeType));

  const interGroupImports = [...interCounts.entries()].map(([key, count]) => {
    const [from, to] = key.split('\u0000');
    return { from, to, count };
  }).sort((a, b) => a.from.localeCompare(b.from) || a.to.localeCompare(b.to));

  const intraGroupDensity = {};
  for (const group of Object.keys(directoryGroups)) {
    let internalEdges = 0;
    let totalEdges = 0;
    for (const edge of importEdges) {
      const from = groupById.get(edge.source);
      const to = groupById.get(edge.target);
      if (from === group || to === group) totalEdges += 1;
      if (from === group && to === group) internalEdges += 1;
    }
    intraGroupDensity[group] = { internalEdges, totalEdges, density: totalEdges ? Number((internalEdges / totalEdges).toFixed(4)) : 0 };
  }

  const patterns = [
    [/^(routes?|api|controllers?|endpoints?|handlers?|serializers?|routers?|blueprints?)$/i, 'api'],
    [/^(services?|core|lib|domain|logic|internal|signals?|mailers?|jobs?|channels?|composables?)$/i, 'service'],
    [/^(models?|db|data|persistence|repositories?|entities?|migrations?|sql|database|schema)$/i, 'data'],
    [/^(components?|views?|pages?|ui|layouts?|screens?)$/i, 'ui'],
    [/^(middleware|plugins?|interceptors?|guards?)$/i, 'middleware'],
    [/^(utils?|helpers?|common|shared|tools|pkg|templatetags)$/i, 'utility'],
    [/^(config|constants?|env|settings|management|commands?)$/i, 'config'],
    [/^(__tests__|tests?|specs?)$/i, 'test'],
    [/^(types?|interfaces?|schemas?|contracts?|dtos?|requests?|responses?)$/i, 'types'],
    [/^hooks$/i, 'hooks'],
    [/^(store|state|reducers?|actions?|slices?)$/i, 'state'],
    [/^(assets?|static|public)$/i, 'assets'],
    [/^(docs?|documentation|wiki)$/i, 'documentation'],
    [/^(deploy|deployment|infra|infrastructure|k8s|kubernetes|helm|charts|terraform|tf|docker)$/i, 'infrastructure'],
    [/^(\.github|\.gitlab|\.circleci)$/i, 'ci-cd'],
    [/^(bin|cmd)$/i, 'entry'],
  ];
  const patternMatches = {};
  for (const group of Object.keys(directoryGroups)) {
    const match = patterns.find(([pattern]) => pattern.test(group));
    if (match) patternMatches[group] = match[1];
  }

  const lowerPaths = fileNodes.map((node) => normalize(node.filePath).toLowerCase());
  const infraFiles = fileNodes.filter((node) => {
    const p = normalize(node.filePath).toLowerCase();
    return p.endsWith('dockerfile') || /(^|\/)docker-compose[^/]*\.(yml|yaml)$/.test(p) || p.endsWith('.tf') || p.endsWith('.tfvars') || p.includes('/k8s/') || p.includes('/kubernetes/') || p.includes('/helm/') || p.startsWith('.github/workflows/') || p === '.gitlab-ci.yml' || p.endsWith('/jenkinsfile');
  }).map((node) => normalize(node.filePath)).sort();
  const deploymentTopology = {
    hasDockerfile: lowerPaths.some((p) => p.endsWith('dockerfile')),
    hasCompose: lowerPaths.some((p) => /(^|\/)docker-compose[^/]*\.(yml|yaml)$/.test(p)),
    hasK8s: lowerPaths.some((p) => p.includes('/k8s/') || p.includes('/kubernetes/') || p.includes('/helm/')),
    hasTerraform: lowerPaths.some((p) => p.endsWith('.tf') || p.endsWith('.tfvars')),
    hasCI: lowerPaths.some((p) => p.startsWith('.github/workflows/') || p === '.gitlab-ci.yml' || p.endsWith('/jenkinsfile')),
    infraFiles,
  };

  const dataPipeline = {
    schemaFiles: fileNodes.filter((node) => node.type === 'schema' || /(^|\/)(schemas?\.py|schema\.(graphql|gql|proto|prisma|sql))$/i.test(normalize(node.filePath))).map((node) => normalize(node.filePath)).sort(),
    migrationFiles: fileNodes.filter((node) => /(^|\/)migrations?\//i.test(normalize(node.filePath)) || /\.(sql)$/i.test(normalize(node.filePath))).map((node) => normalize(node.filePath)).sort(),
    dataModelFiles: fileNodes.filter((node) => (node.tags ?? []).some((tag) => ['data-model', 'domain-model', 'persistence'].includes(tag)) || /(^|\/)(models?|storage)\.py$/i.test(normalize(node.filePath))).map((node) => normalize(node.filePath)).sort(),
    apiHandlerFiles: fileNodes.filter((node) => (node.tags ?? []).some((tag) => ['api-handler', 'routing'].includes(tag)) || /(^|\/)api\//i.test(normalize(node.filePath))).map((node) => normalize(node.filePath)).sort(),
  };

  const groupsWithDocsSet = new Set();
  for (const node of fileNodes) if (node.type === 'document' || /\.(md|rst)$/i.test(normalize(node.filePath))) groupsWithDocsSet.add(groupFor(node));
  const groupNames = Object.keys(directoryGroups);
  const docCoverage = {
    groupsWithDocs: groupsWithDocsSet.size,
    totalGroups: groupNames.length,
    coverageRatio: groupNames.length ? Number((groupsWithDocsSet.size / groupNames.length).toFixed(4)) : 0,
    undocumentedGroups: groupNames.filter((group) => !groupsWithDocsSet.has(group)).sort(),
  };

  const pairCounts = new Map();
  for (const item of interGroupImports) {
    if (item.from === item.to) continue;
    const pair = [item.from, item.to].sort();
    const key = pair.join('\u0000');
    const data = pairCounts.get(key) ?? { a: pair[0], b: pair[1], ab: 0, ba: 0 };
    if (item.from === data.a) data.ab += item.count; else data.ba += item.count;
    pairCounts.set(key, data);
  }
  const dependencyDirection = [];
  for (const data of pairCounts.values()) {
    if (data.ab > data.ba) dependencyDirection.push({ dependent: data.a, dependsOn: data.b, count: data.ab });
    else if (data.ba > data.ab) dependencyDirection.push({ dependent: data.b, dependsOn: data.a, count: data.ba });
    else dependencyDirection.push({ dependent: data.a, dependsOn: data.b, count: data.ab, reciprocal: true });
  }
  dependencyDirection.sort((a, b) => a.dependent.localeCompare(b.dependent) || a.dependsOn.localeCompare(b.dependsOn));

  const result = {
    scriptCompleted: true,
    commonPathPrefix: common.length ? `${common.join('/')}/` : '',
    directoryGroups,
    nodeTypeGroups,
    directoryAdjacency,
    crossCategoryEdges,
    interGroupImports,
    intraGroupDensity,
    patternMatches,
    deploymentTopology,
    dataPipeline,
    docCoverage,
    dependencyDirection,
    fileStats: {
      totalFileNodes: fileNodes.length,
      filesPerGroup: Object.fromEntries(Object.entries(directoryGroups).map(([group, ids]) => [group, ids.length])),
      nodeTypeCounts: Object.fromEntries(Object.entries(nodeTypeGroups).map(([type, ids]) => [type, ids.length])),
    },
    fileFanIn,
    fileFanOut,
  };
  fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
}

try {
  main();
} catch (error) {
  console.error(error?.stack ?? String(error));
  process.exit(1);
}
