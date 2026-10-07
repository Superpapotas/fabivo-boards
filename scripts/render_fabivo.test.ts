// Copy into the authorized Fabivo checkout at src/tmpcheck/render_fabivo.test.ts.
// Run with Vitest. This adapter needs the app reader/renderer source.
import { test, expect } from 'vitest';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { renderModelObservationIsoPane } from '../features/modeler/agent/modelObservationSheet';
import type { ModelDocument } from '../features/modeler/modelerTypes';

test('render actual archived medoid documents without changing geometry', () => {
  const root = process.env.SHOWCASE_ARCHIVE;
  const out = process.env.SHOWCASE_RGBA;
  if (!root || !out) throw new Error('Set SHOWCASE_ARCHIVE and SHOWCASE_RGBA');
  mkdirSync(out, { recursive: true });
  const rows = JSON.parse(readFileSync(`${root}/cons-10.json`, 'utf8')) as {case:string;pick:string}[];
  expect(rows).toHaveLength(19);
  for (const row of rows) {
    const doc = JSON.parse(readFileSync(`${row.pick}-trace/${row.case}/document-prod.json`, 'utf8')) as ModelDocument;
    const geometry = JSON.stringify({panels:doc.panels,design:doc.design});
    doc.materials = doc.materials.map(m => ({...m,color:'#d3c6af'}));
    expect(JSON.stringify({panels:doc.panels,design:doc.design})).toBe(geometry);
    const pane = renderModelObservationIsoPane(doc, {width:1000,height:1000,padding:65});
    writeFileSync(`${out}/${row.case}.rgba`, pane.pixels);
  }
}, 120000);
