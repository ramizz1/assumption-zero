#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const uaDir = process.argv[2];
const commit = process.argv[3];
const scan = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'scan-result.json'), 'utf8'));
const assembled = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'assembled-graph.json'), 'utf8'));
const rawLayers = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'layers.json'), 'utf8'));
const rawTour = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'tour.json'), 'utf8'));
const layers = Array.isArray(rawLayers) ? rawLayers : (rawLayers.layers || []);
const tour = (Array.isArray(rawTour) ? rawTour : (rawTour.steps || [])).sort((a, b) => a.order - b.order);
const graph = {
  version: '1.0.0',
  project: {
    name: scan.name,
    languages: scan.languages,
    frameworks: scan.frameworks,
    description: scan.description,
    analyzedAt: new Date().toISOString(),
    gitCommitHash: commit,
  },
  nodes: assembled.nodes,
  edges: assembled.edges,
  layers,
  tour,
};
fs.writeFileSync(path.join(uaDir, 'intermediate', 'assembled-graph.json'), JSON.stringify(graph, null, 2));
