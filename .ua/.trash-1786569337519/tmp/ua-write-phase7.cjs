#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const projectRoot = process.argv[2];
const uaDir = process.argv[3];
const commit = process.argv[4];
const scan = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'scan-result.json'), 'utf8'));
const finalGraphPath = path.join(uaDir, 'intermediate', 'assembled-graph.json');
fs.copyFileSync(finalGraphPath, path.join(uaDir, 'knowledge-graph.json'));
fs.writeFileSync(path.join(uaDir, 'intermediate', 'fingerprint-input.json'), JSON.stringify({
  projectRoot,
  sourceFilePaths: scan.files.map(file => file.path),
  gitCommitHash: commit,
}, null, 2));
