#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const uaDir = process.argv[2];
const commit = process.argv[3];
const scan = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'scan-result.json'), 'utf8'));
fs.writeFileSync(path.join(uaDir, 'meta.json'), JSON.stringify({
  lastAnalyzedAt: new Date().toISOString(),
  gitCommitHash: commit,
  version: '1.0.0',
  analyzedFiles: scan.totalFiles,
}, null, 2));
