#!/usr/bin/env node
/** Structural smoke checks for the Titan Meridian Capital estate.
 *  No dependencies, no network — file existence + content markers that
 *  would catch a broken restructure, a renamed anchor, or stripped
 *  disclaimers before they deploy.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
let failures = 0;

function check(desc, ok) {
  if (ok) {
    console.log(`  ok  ${desc}`);
  } else {
    failures += 1;
    console.error(`FAIL  ${desc}`);
  }
}

function file(rel) {
  const p = path.join(root, rel);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : null;
}

/* ── Fund website ─────────────────────────────────────────────── */
const fund = file('index.html');
check('fund site exists (index.html)', !!fund);
if (fund) {
  check('fund site: Titan Meridian Capital branding', fund.includes('TITAN MERIDIAN CAPITAL'));
  check('fund site: links to platform/', fund.includes('href="platform/"'));
  check('fund site: links to clients/', fund.includes('href="clients/"'));
  check('fund site: links to titan-markets/', fund.includes('href="titan-markets/"'));
  check('fund site: links to family-office/', fund.includes('href="family-office/"'));
  check('fund site: not-an-offer disclaimer present', /not an offer/i.test(fund));
}

/* ── Meridian Terminal ────────────────────────────────────────── */
const term = file('platform/index.html');
check('terminal exists (platform/index.html)', !!term);
if (term) {
  check('terminal: titled Meridian Terminal', term.includes('Meridian Terminal'));
  check('terminal: simulated-data label', /Sim Data|simulated/i.test(term));
  check('terminal: paper book label', /Paper Book|paper/i.test(term));
  check('terminal: reads data/news.json', term.includes('data/news.json'));
  check('terminal: daily loss limit logic', term.includes('DAILY_LIMIT_PCT'));
}

const news = file('platform/data/news.json');
check('news.json exists', !!news);
if (news) {
  let parsed = null;
  try { parsed = JSON.parse(news); } catch (e) { /* handled below */ }
  check('news.json parses', !!parsed);
  check('news.json has items[]', !!parsed && Array.isArray(parsed.items) && parsed.items.length > 0);
}

/* ── Client portal ────────────────────────────────────────────── */
const portal = file('clients/index.html');
check('portal exists (clients/index.html)', !!portal);
if (portal) {
  check('portal: demo gate present', portal.includes('demonstration portal') || portal.includes('Demonstration portal'));
  check('portal: sample-data ribbon', /sample data/i.test(portal));
  check('portal: noindex meta', portal.includes('noindex'));
}

/* ── Titan Markets division site ──────────────────────────────── */
const desk = file('titan-markets/index.html');
check('desk site exists (titan-markets/index.html)', !!desk);
if (desk) {
  check('desk site: Titan Markets branding', desk.includes('TITAN MARKETS LLC'));
  check('desk site: links back to Meridian estate', desk.includes('href="../"'));
}
check('promo reel exists (titan-markets/promo.html)', !!file('titan-markets/promo.html'));

/* ── Blueprint + governance pack ──────────────────────────────── */
check('blueprint page exists (family-office/index.html)', !!file('family-office/index.html'));
[
  'README.md',
  '01_master_blueprint.md',
  '02_investment_policy_statement.md',
  '03_governance_charter.md',
  '04_operations_runbook.md',
  '05_compliance_calendar.md',
  '06_onboarding_checklist.md',
  '07_technology_estate.md',
  '08_security_continuity.md',
].forEach((doc) => {
  check(`governance pack: ${doc}`, !!file(`docs/family_office/${doc}`));
});

/* ── Pipelines ────────────────────────────────────────────────── */
check('news fetch script exists', !!file('scripts/fetch_news.py'));
check('news workflow exists', !!file('.github/workflows/news.yml'));
check('pages workflow exists', !!file('.github/workflows/pages.yml'));

/* ── Result ───────────────────────────────────────────────────── */
if (failures) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log('\nAll smoke checks passed.');
