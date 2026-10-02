"""A self-contained, offline report. No source text, remote assets or telemetry."""

import base64
from collections import Counter
from hashlib import sha256
from html import escape
import json
from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .report import Report


_SCRIPT = """const rows = Array.from(document.querySelectorAll('tbody tr'));
const search = document.querySelector('#search');
const buttons = Array.from(document.querySelectorAll('[data-filter]'));
let severity = 'all';
function update() {
  const query = search.value.toLowerCase();
  let visible = 0;
  rows.forEach(row => {
    const matches = (severity === 'all' || row.dataset.severity === severity)
      && row.textContent.toLowerCase().includes(query);
    row.hidden = !matches;
    if (matches) visible += 1;
  });
  document.querySelector('#visible-count').textContent = visible + (visible === 1 ? ' finding shown' : ' findings shown');
  document.querySelector('#no-results').hidden = visible !== 0;
}
buttons.forEach(button => button.addEventListener('click', () => {
  severity = button.dataset.filter;
  buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  update();
}));
search.addEventListener('input', update);
update();"""


_PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-$script_hash'; base-uri 'none'; form-action 'none'">
<title>Dataset preflight · VLM Data Doctor</title>
<style>
:root{color-scheme:light;--ink:#15272a;--muted:#526469;--paper:#f5f7f5;--line:#dbe3df;--teal:#116453;--red:#a33728;--amber:#865610}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:1200px;padding:34px 36px 44px;margin:auto}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:36px;gap:18px}
.brand{display:flex;align-items:center;gap:12px;font-size:17px;font-weight:750;letter-spacing:-.4px}
.mark{background:var(--ink);border-radius:11px;color:#e5faef;width:38px;height:38px;display:grid;place-items:center;font-size:13px;letter-spacing:-1px}
.tag{font-size:11px;letter-spacing:1.4px;text-transform:uppercase;font-weight:700;color:var(--muted)}
.offline{font-size:12px;padding:6px 11px;background:#e6f1eb;border-radius:30px;color:var(--teal);white-space:nowrap}
.intro{display:flex;justify-content:space-between;gap:28px;align-items:flex-end;margin-bottom:24px}
h1{font-size:44px;line-height:1.1;margin:8px 0 12px;font-weight:730;letter-spacing:-1.8px}
.intro p{margin:0;color:var(--muted);max-width:710px;font-size:15px}
.status{padding:8px 14px;border:1px solid #dbb9b0;border-radius:8px;background:#fbede7;color:var(--red);font-size:12px;font-weight:750;white-space:nowrap;letter-spacing:.5px}
.status.pass{color:var(--teal);background:#e6f1eb;border-color:#a7c9b8}.status.review{color:var(--amber);background:#fff4dc;border-color:#e4cca2}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0 18px}
.stat{padding:20px 22px;background:#fff;border:1px solid var(--line);border-radius:12px}
.stat small{font-size:12px;color:var(--muted)}.stat strong{display:block;font-size:36px;line-height:1.2;letter-spacing:-1px;margin:8px 0 5px}
.stat span{font-size:11px;color:var(--muted)}.stat.error strong{color:var(--red)}.stat.warning strong{color:var(--amber)}
.overview{display:grid;grid-template-columns:1.12fr 1fr;gap:18px;margin-bottom:26px}
.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px 24px}
h2{font-size:16px;letter-spacing:-.3px;margin:0 0 17px}.bar-row{display:grid;grid-template-columns:minmax(0,1fr) 100px 22px;gap:12px;align-items:center;margin:10px 0;font-size:11px}
.bar-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bar-track{height:6px;border-radius:20px;background:#ecf0ed;overflow:hidden}.bar-fill{height:100%;background:#477d6d;border-radius:20px}
.next{display:flex;gap:13px;margin:12px 0}.step{width:24px;height:24px;flex:none;background:#edf2ee;color:var(--teal);display:grid;place-items:center;border-radius:50%;font-size:11px;font-weight:bold}
.next strong{font-size:12px}.next p{font-size:12px;margin:3px 0 0;color:var(--muted)}
.findings{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.section-head{padding:22px 24px 0;display:flex;justify-content:space-between;align-items:center}.section-head h2{margin:0}.count{font-size:12px;color:var(--muted)}
.controls{padding:18px 24px;display:flex;gap:16px;justify-content:space-between;align-items:center}
.filters{display:flex;gap:4px;background:#eff3f0;padding:4px;border-radius:8px}
button{border:0;border-radius:5px;background:transparent;padding:7px 12px;color:var(--muted);cursor:pointer;font-family:inherit;font-size:12px;font-weight:600;min-height:32px}
button[aria-pressed="true"]{background:#fff;color:var(--ink);box-shadow:0 1px 4px #15272a12}button:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
input{border:1px solid var(--line);border-radius:7px;padding:10px 12px;width:270px;font-family:inherit;font-size:12px;background:#fff;color:var(--ink)}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;text-align:left;min-width:700px}
th{background:#f6f8f6;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:13px 24px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
td{padding:16px 24px;vertical-align:top;border-bottom:1px solid #edf1ee;font-size:12px}tr:last-child td{border-bottom:0}
.severity{display:inline-block;font-size:10px;font-weight:700;padding:3px 8px;background:#fff3dc;color:var(--amber);border-radius:4px;text-transform:uppercase}
.severity.error{background:#fbeae3;color:var(--red)}code{font:11px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;color:#244b42}
.advice{color:var(--muted);max-width:430px}.field{display:block;color:var(--muted);font-size:10px;margin-top:4px}
.empty{padding:24px;text-align:center;color:var(--muted);font-size:13px}[hidden]{display:none!important}
details{margin-top:20px;border:1px solid var(--line);border-radius:9px;background:#fff;padding:15px 20px}
summary{cursor:pointer;font-size:12px;font-weight:650}pre{overflow:auto;font-size:11px;line-height:1.7;color:var(--muted)}
footer{display:flex;justify-content:space-between;gap:20px;font-size:11px;color:var(--muted);margin-top:20px}
.note{font-size:11px;color:var(--muted);margin:12px 0 0}
@media(max-width:760px){.wrap{padding:22px 18px}.intro{display:block}h1{font-size:34px}.status{display:inline-block;margin-top:16px}.stats{grid-template-columns:repeat(2,1fr)}.overview{grid-template-columns:1fr}.controls{align-items:stretch;flex-direction:column}input{width:100%}.tag{font-size:9px}header{margin-bottom:26px}.section-head{gap:10px}footer{flex-direction:column;gap:6px}.stat{padding:16px}}
@media(max-width:760px){table{min-width:0}.table-scroll{overflow:visible}thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}tbody tr{display:block;padding:16px 22px;border-top:1px solid var(--line)}td{display:block;border:0;padding:3px 0}.advice{max-width:none;margin-top:5px}.field{display:inline;margin-left:8px}td code{overflow-wrap:anywhere}td:nth-child(3){color:var(--muted)}}
@media print{.controls,details{display:none}.wrap{max-width:none;padding:0}.table-scroll{overflow:visible}table{min-width:0}tr{break-inside:avoid}body{background:white}}
</style>
</head>
<body><main class="wrap">
<header><div class="brand"><span class="mark" aria-hidden="true">VD</span>VLM Data Doctor</div><span class="offline">Offline · Read-only · CPU</span></header>
<section class="intro"><div><div class="tag">Image-text SFT / Data quality report</div><h1>Dataset preflight.</h1><p>$subtitle</p></div><span class="status $status_class">$status</span></section>
<section class="stats" aria-label="Audit summary">
<div class="stat"><small>Source records</small><strong>$records</strong><span>$split_counts</span></div>
<div class="stat error"><small>Errors</small><strong>$errors</strong><span>Findings that block this profile</span></div>
<div class="stat warning"><small>Warnings</small><strong>$warnings</strong><span>Review against your task policy</span></div>
<div class="stat"><small>Decoded image files</small><strong>$images</strong><span>Unique resolved paths</span></div>
</section>
<section class="overview">
<div class="panel"><h2>Findings by rule</h2>$bars<p class="note">Counts are findings, not distinct failed records. Showing up to six rules.</p></div>
<div class="panel"><h2>Your next steps</h2>
<div class="next"><span class="step">1</span><div><strong>Review the affected rows</strong><p>Resolve errors and decide whether warnings violate your split policy.</p></div></div>
<div class="next"><span class="step">2</span><div><strong>Re-run and preserve the evidence</strong><p>Archive the JSON report, input hashes and experiment configuration.</p></div></div>
<div class="next"><span class="step">3</span><div><strong>Run a small training smoke test</strong><p>Template, tokenizer and model behavior still need separate verification.</p></div></div>
</div></section>
<section class="findings" aria-label="Detailed findings">
<div class="section-head"><h2>Review queue</h2><span id="visible-count" class="count" role="status" aria-live="polite">$findings_count findings</span></div>
<div class="controls"><div class="filters" role="group" aria-label="Filter severity"><button type="button" data-filter="all" aria-pressed="true">All findings</button><button type="button" data-filter="error" aria-pressed="false">Errors</button><button type="button" data-filter="warning" aria-pressed="false">Warnings</button></div><label><span class="sr-only">Search findings</span><input id="search" type="search" placeholder="Search rules, locations or advice…"></label></div>
<div class="table-scroll"><table><thead><tr><th>Severity</th><th>Rule</th><th>Location</th><th>What to do</th></tr></thead><tbody>$rows</tbody></table></div>
<div id="no-results" class="empty" hidden>No findings match this view.</div>
<noscript><p class="empty">JavaScript is disabled. All findings remain visible; filtering requires JavaScript.</p></noscript>
</section>
<details><summary>Reproducibility manifest · input hashes and settings</summary><pre>$manifest</pre></details>
<footer><span>VLM Data Doctor $version · Report schema 1.1</span><span>These checks do not certify label quality or model performance.</span></footer>
</main><script>$script</script></body></html>
""")


def render_html(report: "Report") -> str:
    rows = []
    for issue in report.issues:
        severity_class = "error" if issue.severity == "error" else "warning"
        rows.append(
            f'<tr data-severity="{escape(issue.severity, quote=True)}">'
            f'<td><span class="severity {severity_class}">{escape(issue.severity)}</span></td>'
            f'<td><code>{escape(issue.code)}</code></td>'
            f'<td>{escape(issue.dataset)}:{issue.row}<span class="field">{escape(issue.field)}</span></td>'
            f'<td class="advice">{escape(issue.message)}</td></tr>'
        )
    counts = Counter(issue.code for issue in report.issues)
    maximum = max(counts.values(), default=1)
    bars = []
    for code, count in counts.most_common(6):
        width = count / maximum * 100
        bars.append(f'<div class="bar-row"><code class="bar-name">{escape(code)}</code>'
                    f'<div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:{width:.2f}%"></div></div>'
                    f'<strong>{count}</strong></div>')
    if not bars:
        bars.append('<p class="note">No findings from the supported checks.</p>')
    status, css = ("ERRORS FOUND", "") if report.errors else (("REVIEW WARNINGS", "review") if report.warnings else ("CHECKS PASSED", "pass"))
    subtitle = ("Review data issues before you start the next training run. Every finding points to a row and a field."
                if report.issues else "No issues found by this profile. Preserve this report and validate the training pipeline next.")
    script_hash = base64.b64encode(sha256(_SCRIPT.encode()).digest()).decode()
    return _PAGE.substitute(
        script_hash=script_hash, script=_SCRIPT, subtitle=subtitle,
        status=status, status_class=css, records=sum(report.records.values()),
        split_counts=escape(" · ".join(f"{key} {value:,}" for key, value in report.records.items())),
        errors=report.errors, warnings=report.warnings, images=report.unique_image_files,
        bars="".join(bars), rows="".join(rows), findings_count=len(report.issues),
        manifest=escape(json.dumps(report.provenance, ensure_ascii=False, indent=2)),
        version=escape(str(report.provenance.get("version", ""))),
    )
