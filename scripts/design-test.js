#!/usr/bin/env node
/**
 * Design validation tests for Claude-style warm color scheme.
 * Run: node scripts/design-test.js
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
let passed = 0;
let failed = 0;

function read(rel) {
  return fs.readFileSync(path.join(ROOT, rel), 'utf-8');
}

function test(name, ok, detail) {
  if (ok) {
    console.log(`  ✓ ${name}`);
    passed++;
  } else {
    console.log(`  ✗ ${name}`);
    if (detail) console.log(`    → ${detail}`);
    failed++;
  }
}

// --- Relative luminance & contrast helpers (WCAG 2.1) ---
function srgbToLinear(c) {
  c = c / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}
function luminance(r, g, b) {
  return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
}
function contrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Parse "R, G, B" from CSS variable value
function parseRGB(str) {
  const m = str.match(/(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  return m ? [+m[1], +m[2], +m[3]] : null;
}

// Extract a CSS variable value from content
function getVar(content, varName) {
  const re = new RegExp(`--color-${varName}\\s*:\\s*([^;]+);`);
  const m = content.match(re);
  return m ? m[1].trim() : null;
}

// ===================== TESTS =====================

console.log('\n=== Color Palette Tests ===');
const scheme = read('assets/css/schemes/soitgoes.css');

// --color-neutral base
const neutralBase = getVar(scheme, 'neutral');
test('--color-neutral is warm white (244,243,238)', neutralBase === '244, 243, 238', `Got: ${neutralBase}`);

// neutral-50 through 900 warm (R >= B)
const neutralSteps = ['50','100','200','300','400','500','600','700','800','900'];
for (const step of neutralSteps) {
  const val = getVar(scheme, `neutral-${step}`);
  const rgb = parseRGB(val);
  test(`neutral-${step} is warm (R≥B)`, rgb && rgb[0] >= rgb[2], `Got: ${val}`);
}

// primary-600 = 193, 95, 60
const p600 = getVar(scheme, 'primary-600');
test('primary-600 is rust-orange (193,95,60)', p600 === '193, 95, 60', `Got: ${p600}`);

// Luminance monotonically decreasing across neutral scale
const neutralLums = neutralSteps.map(s => {
  const rgb = parseRGB(getVar(scheme, `neutral-${s}`));
  return luminance(...rgb);
});
let monotonic = true;
for (let i = 1; i < neutralLums.length; i++) {
  if (neutralLums[i] >= neutralLums[i - 1]) { monotonic = false; break; }
}
test('Neutral luminance monotonically decreasing', monotonic);

// ===================== WCAG Contrast Tests =====================

console.log('\n=== WCAG Contrast Tests ===');

const n900 = parseRGB(getVar(scheme, 'neutral-900'));
const n50 = parseRGB(getVar(scheme, 'neutral-50'));
const n100 = parseRGB(getVar(scheme, 'neutral-100'));
const p600rgb = parseRGB(getVar(scheme, 'primary-600'));

const cr1 = contrastRatio(luminance(...n900), luminance(...n50));
test(`neutral-900 on neutral-50 ≥ 4.5:1 (got ${cr1.toFixed(2)})`, cr1 >= 4.5);

const cr2 = contrastRatio(luminance(...p600rgb), luminance(255, 255, 255));
test(`primary-600 on white ≥ 3:1 (got ${cr2.toFixed(2)})`, cr2 >= 3);

const cr3 = contrastRatio(luminance(...n100), luminance(...n900));
test(`neutral-100 on neutral-900 ≥ 4.5:1 (got ${cr3.toFixed(2)})`, cr3 >= 4.5);

// ===================== Card Template Tests =====================

console.log('\n=== Card Template Tests ===');
const listTpl = read('layouts/project/list.html');
const customCSS = read('assets/css/custom.css');

test('project/list.html has no bg-white', !listTpl.includes('bg-white'));
test('project/list.html has no hover:shadow-xl', !listTpl.includes('hover:shadow-xl'));
test('project/list.html has no hover:-translate-y-1', !listTpl.includes('hover:-translate-y-1'));
test('custom.css has article.group:hover with transform: scale', customCSS.includes('article.group:hover') && customCSS.includes('transform: scale(1.02)'));
test('custom.css has .article-link--card:hover', customCSS.includes('.article-link--card:hover'));
test('custom.css has .bg-white global override', customCSS.includes('.bg-white') && customCSS.includes('--color-neutral-50'));

// ===================== Splash Tests =====================

console.log('\n=== Splash Animation Tests ===');
const extHead = read('layouts/partials/extend-head.html');
const splashTest = read('static/splash-test.html');

// No old blue-gray remnants
test('extend-head.html: no old blue-gray ring (80, 131, 182)', !extHead.includes('80, 131, 182'));
test('extend-head.html: no old blue-gray light (47, 87, 128)', !extHead.includes('47, 87, 128'));
test('extend-head.html: no old dark bg (15, 23, 42)', !extHead.includes('15, 23, 42'));

// New warm colors present
test('extend-head.html: uses warm dark bg (28, 25, 23)', extHead.includes('28, 25, 23'));
test('extend-head.html: uses warm light bg (250, 249, 246)', extHead.includes('250, 249, 246'));
test('extend-head.html: uses rust-orange ring (193, 95, 60)', extHead.includes('193, 95, 60'));

// splash-test.html consistency
test('splash-test.html: no old blue-gray (80, 131, 182)', !splashTest.includes('80, 131, 182'));
test('splash-test.html: no old blue-gray (47, 87, 128)', !splashTest.includes('47, 87, 128'));
test('splash-test.html: uses rust-orange (193, 95, 60)', splashTest.includes('193, 95, 60'));
test('splash-test.html: uses warm dark bg (28, 25, 23)', splashTest.includes('28, 25, 23'));

// ===================== File Integrity Tests =====================

console.log('\n=== File Integrity Tests ===');
const customHeadExists = fs.existsSync(path.join(ROOT, 'layouts/partials/custom/head.html'));
test('custom/head.html does not exist (cleaned up)', !customHeadExists);

// No old blue-gray primary remnants anywhere in modified files
const allContent = scheme + customCSS + extHead + splashTest + listTpl;
test('No old primary (80, 131, 182) remnant in any file', !allContent.includes('80, 131, 182'));
test('No old slate dark (15, 23, 42) remnant in any file', !allContent.includes('15, 23, 42'));

// ===================== Summary =====================

console.log(`\n${'='.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
if (failed > 0) {
  console.log('SOME TESTS FAILED');
  process.exit(1);
} else {
  console.log('ALL TESTS PASSED');
}
