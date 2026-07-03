#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2] || path.join("output", "releases.json");
const outputPath = process.argv[3] || path.join("output", "index.html");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

if (!fs.existsSync(inputPath)) {
  console.error(`[dashboard] input not found: ${inputPath}`);
  process.exit(1);
}

const documentData = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const rows = documentData.releases || [];
if (rows.length === 0) {
  console.error("[dashboard] release rows are empty");
  process.exit(1);
}

const dataScript = JSON.stringify(rows).replaceAll("</", "<\\/");
const metadata = documentData.metadata || {};
const html = `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Python Releases Dashboard</title>
  <style>
    :root { font-family: "Noto Sans JP", "Yu Gothic", sans-serif; color: #1f252b; background: #f4f6f8; }
    * { box-sizing: border-box; }
    body { margin: 0; }
    header { background: #243b53; color: white; padding: 28px max(24px, calc((100vw - 1040px) / 2)); }
    header h1 { margin: 0 0 8px; font-size: clamp(1.5rem, 4vw, 2.25rem); }
    header p { margin: 4px 0; opacity: .9; }
    main { max-width: 1040px; margin: 0 auto; padding: 24px 20px 44px; }
    .toolbar { display: grid; grid-template-columns: minmax(180px, 1fr) 190px; gap: 10px; margin-bottom: 14px; }
    input, select { width: 100%; padding: 10px 12px; border: 1px solid #c9d3dd; border-radius: 6px; font: inherit; background: white; }
    table { width: 100%; border-collapse: collapse; background: white; }
    th, td { padding: 11px 12px; border: 1px solid #dbe2e8; text-align: left; }
    th { background: #eaf0f5; cursor: pointer; user-select: none; }
    tr:nth-child(even) td { background: #fafbfc; }
    a { color: #1f5c99; font-weight: 700; }
    .count { margin: 0 0 8px; color: #5b6670; }
    footer { max-width: 1040px; margin: 0 auto; padding: 0 20px 32px; color: #5b6670; font-size: .86rem; }
    @media (max-width: 700px) { .toolbar { grid-template-columns: 1fr; } .table-wrap { overflow-x: auto; } table { min-width: 720px; } }
  </style>
</head>
<body>
  <header>
    <h1>Python Releases Dashboard</h1>
    <p>Python公式サイトから取得した最近のリリース情報</p>
    <p>生成日時: ${escapeHtml(metadata.generated_at || "-")} / データ元: ${escapeHtml(metadata.source || "-")}</p>
  </header>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="バージョンやURLで検索" aria-label="検索">
      <select id="sort" aria-label="並べ替え">
        <option value="date_desc">公開日 新しい順</option>
        <option value="date_asc">公開日 古い順</option>
        <option value="version_desc">バージョン 降順</option>
        <option value="version_asc">バージョン 昇順</option>
      </select>
    </div>
    <p class="count" id="count"></p>
    <section class="table-wrap">
      <table>
        <thead><tr><th data-sort="version">バージョン</th><th data-sort="published_date">公開日</th><th>詳細URL</th></tr></thead>
        <tbody id="releaseRows"></tbody>
      </table>
    </section>
  </main>
  <footer>スクリプトプログラミング演習2 / HW25A066 嶋田一歩 / JavaScript検索・並べ替え付き</footer>
  <script>
    const releases = ${dataScript};
    const tbody = document.getElementById("releaseRows");
    const search = document.getElementById("search");
    const sort = document.getElementById("sort");
    const count = document.getElementById("count");
    function versionKey(value) {
      return String(value).split(/[^0-9]+/).filter(Boolean).map(Number);
    }
    function compareVersion(a, b) {
      const aa = versionKey(a.version);
      const bb = versionKey(b.version);
      for (let i = 0; i < Math.max(aa.length, bb.length); i++) {
        const diff = (aa[i] || 0) - (bb[i] || 0);
        if (diff) return diff;
      }
      return 0;
    }
    function filteredRows() {
      const q = search.value.trim().toLowerCase();
      const rows = releases.filter((row) => !q || Object.values(row).join(" ").toLowerCase().includes(q));
      rows.sort((a, b) => {
        if (sort.value === "date_asc") return a.published_date.localeCompare(b.published_date);
        if (sort.value === "date_desc") return b.published_date.localeCompare(a.published_date);
        if (sort.value === "version_asc") return compareVersion(a, b);
        return compareVersion(b, a);
      });
      return rows;
    }
    function render() {
      const rows = filteredRows();
      count.textContent = rows.length + "件を表示中";
      tbody.innerHTML = rows.map((row) => '<tr><td>Python ' + row.version + '</td><td>' + row.published_date + '</td><td><a href="' + row.detail_url + '">' + row.detail_url + '</a></td></tr>').join("");
    }
    document.querySelectorAll("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
      const key = th.dataset.sort;
      sort.value = key === "version" ? "version_desc" : "date_desc";
      render();
    }));
    search.addEventListener("input", render);
    sort.addEventListener("change", render);
    render();
  </script>
</body>
</html>`;

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, html, "utf8");
console.log(`[dashboard] generated: ${outputPath}`);
console.log(`[dashboard] rows: ${rows.length}`);

