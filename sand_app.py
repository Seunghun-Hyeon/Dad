import sys
import os
import webbrowser
import threading
import json
import csv
import re
import urllib.request
from datetime import date, datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# 실행 파일(.exe)로 실행될 때도 항상 실행 파일이 있는 실제 폴더에 sand_db.json 저장
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "sand_db.json")
PORT = 8765

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>주물사 시험성적 관리 및 기술보고서 시스템 (다중 회사 지원)</title>
<style>
  * { box-sizing: border-box; font-family: "Malgun Gothic", "Apple SD Gothic Neo", -apple-system, sans-serif; }
  body { margin: 0; background: #f1f5f9; color: #0f172a; padding: 14px; }

  /* 최상단 회사 선택 바 */
  .company-bar {
    background: #1e3a8a;
    color: #ffffff;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  }
  .company-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .company-left label { font-size: 14px; font-weight: 800; letter-spacing: -0.3px; }
  .company-select {
    padding: 6px 12px;
    border-radius: 6px;
    border: 2px solid #93c5fd;
    font-size: 14px;
    font-weight: 800;
    color: #0f172a;
    background: #ffffff;
    min-width: 250px;
    cursor: pointer;
  }
  .btn-comp-add { background: #2563eb; color: #fff; border: 1px solid #93c5fd; }
  .btn-comp-add:hover { background: #1d4ed8; }
  .btn-comp-bulk { background: #0d9488; color: #fff; border: 1px solid #5eead4; }
  .btn-comp-bulk:hover { background: #0f766e; }
  .btn-comp-del { background: #991b1b; color: #fecaca; border: 1px solid #f87171; }
  .btn-comp-del:hover { background: #7f1d1d; color: #fff; }
  .btn-exit { background: #0f172a; color: #f8fafc; border: 1px solid #64748b; }
  .btn-exit:hover { background: #334155; }

  /* 상단 공통 컨트롤 바 */
  .card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
  .top-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
  .meta-grid { display: grid; grid-template-columns: repeat(4, auto); gap: 6px 12px; align-items: center; font-size: 12.5px; }
  .meta-grid label { font-weight: 700; color: #334155; }
  .meta-grid input { background: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 8px; font-weight: 600; width: 145px; }
  .ctrl-box { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .ctrl-box label { font-weight: 700; color: #1e3a8a; font-size: 13.5px; }
  .ctrl-box input[type="date"] { padding: 5px 8px; border: 1px solid #94a3b8; border-radius: 6px; font-weight: 700; font-size: 13.5px; }

  button { border: none; border-radius: 6px; padding: 8px 13px; font-weight: 700; font-size: 12.5px; cursor: pointer; transition: 0.15s; }
  .btn-shift { background: #1d4ed8; color: #fff; font-size: 13.5px; padding: 8px 16px; }
  .btn-shift:hover { background: #1e40af; }
  .btn-save { background: #15803d; color: #fff; }
  .btn-save:hover { background: #166534; }
  .btn-cancel { background: #dc2626; color: #fff; }
  .btn-cancel:hover { background: #b91c1c; }
  .btn-import { background: #475569; color: #fff; }
  .btn-import:hover { background: #334155; }
  .btn-print { background: #0f172a; color: #fff; }
  .btn-print:hover { background: #334155; }
  .btn-del { background: #fee2e2; color: #b91c1c; padding: 5px 10px; font-size: 12px; }

  /* 탭 전환 버튼 */
  .tabs { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
  .tab-group { display: flex; gap: 6px; }
  .tab-btn { background: #e2e8f0; color: #334155; padding: 9px 18px; border-radius: 6px; font-size: 13.5px; }
  .tab-btn.active { background: #1e3a8a; color: #ffffff; }
  .badge-total { background: #dbeafe; color: #1e3a8a; font-weight: 700; font-size: 12.5px; padding: 6px 12px; border-radius: 20px; border: 1px solid #bfdbfe; }

  /* 입력 화면 레이아웃 */
  .main-grid { display: grid; grid-template-columns: 510px 1fr; gap: 12px; align-items: start; }
  h2 { margin: 0 0 10px 0; font-size: 14.5px; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
  .form-split { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .field-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; font-size: 12px; }
  .field-row input { width: 92px; text-align: right; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 12px; }
  .field-row input:focus { outline: none; border-color: #2563eb; background: #eff6ff; }
  .sieve-title { font-weight: 700; font-size: 12px; color: #475569; margin-bottom: 6px; }

  .kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 10px; }
  .kpi { border-radius: 6px; padding: 10px; border: 1px solid #cbd5e1; }
  .kpi .t { font-size: 11px; font-weight: 700; color: #475569; }
  .kpi .v { font-size: 19px; font-weight: 800; text-align: right; margin-top: 4px; }
  .kpi.blue { background: #eff6ff; border-color: #bfdbfe; } .kpi.blue .v { color: #1d4ed8; }
  .kpi.green { background: #f0fdf4; border-color: #bbf7d0; } .kpi.green .v { color: #15803d; }
  .kpi.yellow { background: #fefce8; border-color: #fef08a; } .kpi.yellow .v { color: #a16207; }
  .kpi.purple { background: #faf5ff; border-color: #e9d5ff; } .kpi.purple .v { color: #7e22ce; }

  .sieve-bar { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; font-size: 12px; color: #334155; }
  .table-wrap { max-height: 450px; overflow: auto; border: 1px solid #cbd5e1; border-radius: 6px; }
  table.hist-tbl { width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; }
  table.hist-tbl th { background: #1e3a8a; color: #fff; padding: 8px 6px; position: sticky; top: 0; }
  table.hist-tbl td { padding: 7px 6px; border-bottom: 1px solid #e2e8f0; cursor: pointer; }
  table.hist-tbl tr:hover td { background: #f1f5f9; }
  table.hist-tbl tr.active td { background: #dbeafe; font-weight: 700; }

  /* 결과보고서 A4 양식 */
  .report-container { display: none; flex-direction: column; align-items: center; gap: 24px; padding-bottom: 30px; }
  .a4-page {
    width: 210mm;
    min-height: 292mm;
    background: #ffffff;
    border: 1px solid #94a3b8;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    padding: 12mm 12mm 10mm 12mm;
    color: #000000;
  }
  .rep-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; font-size: 12px; line-height: 1.45; }
  .rep-header-left { padding-left: 16px; }
  .rep-header-left .cust { font-size: 15px; font-weight: 800; }
  .rep-header-left .line-name { font-size: 13px; font-weight: 800; text-decoration: underline; margin-top: 6px; display: inline-block; }
  .rep-header-right { padding-right: 12px; font-size: 12.5px; }
  .rep-header-right table td { padding: 1px 4px; vertical-align: top; }

  table.rep-table { width: 100%; border-collapse: collapse; border: 1.5px solid #000; font-size: 11px; }
  table.rep-table td, table.rep-table th {
    border-top: 1px solid #cbd5e1;
    border-bottom: 1px solid #cbd5e1;
    border-left: 1px dotted #475569;
    border-right: 1px dotted #475569;
    padding: 2.5px 4px;
    height: 19px;
  }
  table.rep-table td.label-col {
    border-left: 1.5px solid #000;
    border-right: 1.5px solid #000;
    text-align: left;
    padding-left: 6px;
    font-weight: 500;
    white-space: nowrap;
  }
  table.rep-table td.val-col { text-align: right; padding-right: 6px; font-variant-numeric: tabular-nums; width: 54px; }
  table.rep-table td.head-val { text-align: center; font-size: 10.5px; font-weight: 600; border-top: none; border-bottom: none; }
  table.rep-table tr.top-border td { border-top: 1.5px solid #000; }
  table.rep-table tr.bottom-border td { border-bottom: 1.5px solid #000; }
  table.rep-table tr.section-banner td {
    border-top: 1.5px solid #000;
    border-bottom: 1.5px solid #000;
    border-left: 1.5px solid #000;
    border-right: 1.5px solid #000;
    text-align: center;
    font-weight: 700;
    font-size: 10.5px;
    background: #ffffff;
    padding: 3px 0;
  }
  .sieve-subtable { width: 100%; border-collapse: collapse; }
  .sieve-subtable td { border: none !important; padding: 0 4px !important; height: 17px !important; font-size: 10.5px; }

  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: repeat(4, 1fr);
    border: 1.5px solid #000;
    height: 238mm;
  }
  .chart-cell {
    border: 0.75px solid #000;
    padding: 6px 8px 4px 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
  }
  .chart-title { font-size: 12px; font-weight: 800; text-align: center; margin-top: 2px; letter-spacing: 0.2px; }
  .chart-cell svg { width: 100%; height: 100%; }

  .toast { position: fixed; bottom: 20px; right: 20px; background: #0f172a; color: #fff; padding: 10px 18px; border-radius: 6px; font-size: 13px; display: none; z-index: 999; }

  @media print {
    body { background: #fff; padding: 0; }
    .no-print { display: none !important; }
    .report-container { display: flex !important; gap: 0; padding: 0; }
    .a4-page { border: none; box-shadow: none; margin: 0; page-break-after: always; }
    .a4-page:last-child { page-break-after: auto; }
  }
</style>
</head>
<body>

<!-- 최상단 회사/라인 전환 바 -->
<div class="company-bar no-print">
  <div class="company-left">
    <label for="company_select">🏢 회사 / 라인 선택:</label>
    <select id="company_select" class="company-select" onchange="switchCompany(this.value)"></select>
    <button class="btn-comp-add" onclick="addNewCompany()">➕ 새 회사 추가</button>
    <button class="btn-comp-bulk" onclick="document.getElementById('bulk_file_import').click()">📂 여러 회사 엑셀 일괄 불러오기</button>
    <input type="file" id="bulk_file_import" accept=".csv,.xls,.xlsx" multiple style="display:none" onchange="handleBulkImportFiles(event)">
    <button class="btn-comp-del" onclick="deleteCurrentCompany()">🗑️ 현재 회사 삭제</button>
  </div>
  <div style="display:flex; align-items:center; gap:10px;">
    <span style="font-size:12px; color:#dbeafe;" id="company_summary_txt"></span>
    <button class="btn-exit" onclick="shutdownApp()">⏻ 프로그램 완전 종료</button>
  </div>
</div>

<!-- 상단 공통 컨트롤 바 -->
<div class="card top-bar no-print">
  <div class="meta-grid">
    <label>수신(Customer):</label><input id="meta_customer" oninput="syncMeta()">
    <label>라인(Line):</label><input id="meta_line" oninput="syncMeta()">
    <label>Copy 1:</label><input id="meta_person" oninput="syncMeta()">
    <label>Copy 2:</label><input id="meta_copy" oninput="syncMeta()">
    <label>주소(Address):</label><input id="meta_address" style="grid-column: span 3; width: 100%;" oninput="syncMeta()">
  </div>
  <div class="ctrl-box">
    <label>Date (오늘 날짜):</label>
    <input type="date" id="report_date" onchange="syncMeta()">
    <button class="btn-shift" onclick="insertShiftColumn()">＋ 입력 (세로줄 한 칸 밀기)</button>
    <button class="btn-save" onclick="saveAll()">💾 저장하기</button>
    <button class="btn-cancel" onclick="cancelInput()">↩️ 입력 취소</button>
    <button class="btn-import" onclick="document.getElementById('file_import').click()">📂 이 회사 엑셀 불러오기</button>
    <input type="file" id="file_import" accept=".csv,.xls,.xlsx" style="display:none" onchange="handleImportFile(event)">
    <button class="btn-print" onclick="openReportAndPrint()">🖨️ 성적서 인쇄 / PDF</button>
  </div>
</div>

<!-- 화면 전환 탭 -->
<div class="tabs no-print">
  <div class="tab-group">
    <button class="tab-btn active" id="tab_input_btn" onclick="switchTab('input')">1. 데이터 입력 및 최근 8개 이력</button>
    <button class="tab-btn" id="tab_report_btn" onclick="switchTab('report')">2. 결과보고서 양식 (최근 8개 성적표 + 그래프)</button>
  </div>
  <div class="badge-total" id="badge_total">백데이터 누적: 총 0건 (화면 표시: 최근 8건)</div>
</div>

<!-- [탭 1] 데이터 입력 및 누적 이력 -->
<div id="view_input" class="main-grid no-print">
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #e2e8f0; padding-bottom:6px; margin-bottom:10px;">
      <h2 id="form_title" style="margin:0; border:none; padding:0;">1. 측정 데이터 입력 (현재 선택: 1열 - 최신)</h2>
      <button class="btn-cancel" style="padding:4px 10px; font-size:11.5px;" onclick="cancelInput()">↩️ 입력 취소</button>
    </div>
    <div class="form-split">
      <div id="basic_inputs"></div>
      <div>
        <div class="sieve-title">[체가름 실제 잔류무게 (g)]</div>
        <div id="sieve_inputs"></div>
      </div>
    </div>
  </div>

  <div>
    <div class="card">
      <h2>2. 자동 연산 결과 (입력 즉시 실시간 계산)</h2>
      <div class="kpi-grid">
        <div class="kpi blue"><div class="t">실용점토분 (WB)</div><div class="v" id="kpi_wb">0.00</div></div>
        <div class="kpi blue"><div class="t">유효점토분 (AB)</div><div class="v" id="kpi_ab">0.00</div></div>
        <div class="kpi green"><div class="t">믹싱효율 (%)</div><div class="v" id="kpi_me">0.0 %</div></div>
        <div class="kpi yellow"><div class="t">전점토분 (Clay %)</div><div class="v" id="kpi_clay">0.00 %</div></div>
        <div class="kpi purple"><div class="t">입도지수 (GFN)</div><div class="v" id="kpi_gfn">0.00</div></div>
      </div>
      <div class="sieve-bar" id="sieve_pct_bar">체가름 잔류율(%): -</div>
    </div>

    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <h2 style="margin:0; border:none; padding:0;" id="hist_heading">3. 최근 8개 시험 이력 (맨 위 1열이 가장 최신)</h2>
        <div style="display:flex; align-items:center; gap:10px;">
          <label style="font-size:12px; font-weight:700; color:#334155; cursor:pointer;">
            <input type="checkbox" id="chk_show_all" onchange="updateCalcAndTable()"> 전체 백데이터 모두 보기
          </label>
          <button class="btn-del" onclick="deleteSelected()">선택 열 삭제</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="hist-tbl">
          <thead>
            <tr>
              <th>열 순서</th><th>Date</th><th>CS No.</th><th>충진도(%)</th><th>수분(%)</th>
              <th>생형강도</th><th>실용점토</th><th>유효점토</th><th>믹싱효율(%)</th><th>전점토(%)</th><th>입도지수</th>
            </tr>
          </thead>
          <tbody id="hist_tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- [탭 2] 결과보고서 양식 (1페이지 성적표 + 2페이지 8개 추이 그래프) -->
<div id="view_report" class="report-container">
  <div class="a4-page" id="report_page_1"></div>
  <div class="a4-page" id="report_page_2"></div>
</div>

<div class="toast" id="toast">저장되었습니다.</div>

<script>
const SIEVES = [
  ["3.35 mm", "No. 6", 3], ["1.70 mm", "No. 12", 5], ["850 µm", "No. 20", 10],
  ["600 µm", "No. 30", 20], ["425 µm", "No. 40", 30], ["300 µm", "No. 50", 40],
  ["212 µm", "No. 70", 50], ["150 µm", "No. 100", 70], ["106 µm", "No. 140", 100],
  ["75 µm", "No. 200", 140], ["53 µm", "No. 270", 200], ["Pan", "Pan", 300]
];

const BASIC_FIELDS = [
  ["confirm_date", "Confirmation date", "date"],
  ["request_date", "Request date", "date"],
  ["cs_no", "Customer Service No.", "text"],
  ["cb", "충진도, Compactability (%)", "number"],
  ["moisture", "수분, Moisture (% by wt)", "number"],
  ["density", "시편무게, Density (g)", "number"],
  ["perm", "통기도, Permeability No.", "number"],
  ["shear", "전단강도, Shear Str.", "number"],
  ["gcs", "생형압축강도, GCS", "number"],
  ["cb_wt", "충진도시편무게 (g)", "number"],
  ["dcs", "건태강도, Dry Comp.", "number"],
  ["wts", "습태인장강도, Wet Tensile", "number"],
  ["init_wt", "건조시료 초기무게 (g)", "number"],
  ["mb_clay", "활성점토분, Active Clay", "number"],
  ["vm", "휘발분, V. Combustile (%)", "number"],
  ["loi", "작열감량, LOI (%)", "number"]
];

let rootDB = { active_id: "", companies: {} };
let savedSnapshot = "";
let selectedIdx = 0;

function curCompany() {
  return rootDB.companies[rootDB.active_id];
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function fmtShortDate(iso) {
  if (!iso) return "";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  return `${parts[0].slice(2)}-${parseInt(parts[1], 10)}-${parseInt(parts[2], 10)}`;
}

function fmtDotDate(iso) {
  if (!iso) return "";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  return `${parts[0]}.${parseInt(parts[1], 10)}.${parseInt(parts[2], 10)}`;
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.display = "block";
  setTimeout(() => { t.style.display = "none"; }, 2800);
}

async function shutdownApp() {
  if (JSON.stringify(rootDB) !== savedSnapshot) {
    const saveFirst = confirm("저장하지 않은 입력 내용이 있습니다. 저장 후 프로그램을 종료하시겠습니까?");
    if (saveFirst) await saveAll(true);
  } else {
    if (!confirm("프로그램을 완전히 종료하시겠습니까?")) return;
  }
  await fetch("/api/shutdown", { method: "POST" }).catch(() => {});
  document.body.innerHTML = "<div style='padding:40px; text-align:center; font-size:18px; font-weight:700;'>프로그램이 안전하게 종료되었습니다. 이 브라우저 창을 닫으셔도 됩니다.</div>";
}

function renderCompanyDropdown() {
  const sel = document.getElementById("company_select");
  sel.innerHTML = "";
  const ids = Object.keys(rootDB.companies);
  ids.forEach(cid => {
    const c = rootDB.companies[cid];
    const opt = document.createElement("option");
    opt.value = cid;
    const cust = c.meta.customer || "미지정 회사";
    const line = c.meta.line ? ` (${c.meta.line})` : "";
    opt.textContent = `${cust}${line} - ${c.records.length}건`;
    if (cid === rootDB.active_id) opt.selected = true;
    sel.appendChild(opt);
  });
  document.getElementById("company_summary_txt").textContent =
    `등록 회사: 총 ${ids.length}곳`;
}

function switchCompany(newId) {
  if (!rootDB.companies[newId]) return;
  if (JSON.stringify(rootDB) !== savedSnapshot) {
    const ok = confirm("[더블체크] 현재 회사에 저장하지 않은 입력/수정 내용이 있습니다.\n저장하지 않고 다른 회사로 이동하시겠습니까?");
    if (!ok) {
      document.getElementById("company_select").value = rootDB.active_id;
      return;
    }
    rootDB = JSON.parse(savedSnapshot);
  }
  rootDB.active_id = newId;
  const comp = curCompany();
  if (!comp.meta.report_date) comp.meta.report_date = todayStr();
  applyMetaToInputs();
  renderCompanyDropdown();
  loadRecordToForm(0);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  saveAll(true);
  showToast(`[${comp.meta.customer} - ${comp.meta.line}] 데이터로 전환되었습니다.`);
}

function addNewCompany() {
  if (JSON.stringify(rootDB) !== savedSnapshot) {
    alert("새 회사를 추가하기 전에 먼저 현재 회사의 변경사항을 [저장하기] 또는 [입력 취소] 해주세요.");
    return;
  }
  const custName = prompt("추가할 회사명(수신처)을 입력하세요:\n(예: 한국주철(주))");
  if (!custName || !custName.trim()) return;
  const lineName = prompt("해당 회사의 라인명을 입력하세요:\n(예: DISA line, FBM line 등)", "DISA line") || "";

  const newId = "comp_" + Date.now();
  const d = todayStr();
  const newRec = {
    confirm_date: d,
    request_date: d,
    cs_no: "DKY-" + d.slice(5).replace("-", ""),
    cb: "", moisture: "", density: "", perm: "", shear: "", gcs: "",
    cb_wt: "", dcs: "", wts: "", init_wt: "50.0", mb_clay: "", vm: "", loi: ""
  };
  for (let i = 0; i < 12; i++) newRec[`sieve_${i}`] = "0.0";

  rootDB.companies[newId] = {
    meta: {
      customer: custName.trim(),
      address: "",
      tel: "041-337-7250~2",
      fax: "041-338-3686",
      line: lineName.trim(),
      person: "",
      copy: "",
      report_date: d
    },
    records: [newRec]
  };
  rootDB.active_id = newId;
  applyMetaToInputs();
  renderCompanyDropdown();
  loadRecordToForm(0);
  saveAll(true);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast(`새 회사 [${custName.trim()}]가 추가되었습니다!`);
}

function deleteCurrentCompany() {
  const ids = Object.keys(rootDB.companies);
  if (ids.length <= 1) {
    alert("최소 1개의 회사는 유지되어야 합니다.");
    return;
  }
  const comp = curCompany();
  const label = `${comp.meta.customer} (${comp.meta.line})`;
  if (!confirm(`[더블체크] '${label}' 회사와 누적된 모든 시험 데이터(${comp.records.length}건)를 완전히 삭제하시겠습니까?`)) return;

  delete rootDB.companies[rootDB.active_id];
  rootDB.active_id = Object.keys(rootDB.companies)[0];
  applyMetaToInputs();
  renderCompanyDropdown();
  loadRecordToForm(0);
  saveAll(true);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast(`'${label}' 회사가 삭제되었습니다.`);
}

function switchTab(tab) {
  const isInput = tab === "input";
  document.getElementById("view_input").style.display = isInput ? "grid" : "none";
  document.getElementById("view_report").style.display = isInput ? "none" : "flex";
  document.getElementById("tab_input_btn").classList.toggle("active", isInput);
  document.getElementById("tab_report_btn").classList.toggle("active", !isInput);
  if (!isInput) renderReportPages();
}

function openReportAndPrint() {
  switchTab("report");
  setTimeout(() => window.print(), 150);
}

function syncMeta() {
  const comp = curCompany();
  comp.meta.customer = document.getElementById("meta_customer").value;
  comp.meta.line = document.getElementById("meta_line").value;
  comp.meta.person = document.getElementById("meta_person").value;
  comp.meta.copy = document.getElementById("meta_copy").value;
  comp.meta.address = document.getElementById("meta_address").value;
  comp.meta.report_date = document.getElementById("report_date").value;
  renderCompanyDropdown();
  if (document.getElementById("view_report").style.display === "flex") {
    renderReportPages();
  }
}

function applyMetaToInputs() {
  const m = curCompany().meta;
  document.getElementById("meta_customer").value = m.customer || "";
  document.getElementById("meta_line").value = m.line || "";
  document.getElementById("meta_person").value = m.person || "";
  document.getElementById("meta_copy").value = m.copy || "";
  document.getElementById("meta_address").value = m.address || "";
  document.getElementById("report_date").value = m.report_date || todayStr();
}

function buildForms() {
  const basicDiv = document.getElementById("basic_inputs");
  BASIC_FIELDS.forEach(([key, label, type]) => {
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `<label>${label}</label><input id="inp_${key}" type="${type === 'number' ? 'text' : type}">`;
    basicDiv.appendChild(row);
    row.querySelector("input").addEventListener("input", (e) => {
      curCompany().records[selectedIdx][key] = e.target.value;
      updateCalcAndTable();
    });
  });

  const sieveDiv = document.getElementById("sieve_inputs");
  SIEVES.forEach(([stdN, altN], idx) => {
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `<label>${stdN} (${altN})</label><input id="inp_sieve_${idx}" type="text">`;
    sieveDiv.appendChild(row);
    row.querySelector("input").addEventListener("input", (e) => {
      curCompany().records[selectedIdx][`sieve_${idx}`] = e.target.value;
      updateCalcAndTable();
    });
  });
}

function compute(rec) {
  if (!rec) return null;
  const num = (k, def=0) => { const v = parseFloat(rec[k]); return isNaN(v) ? def : v; };
  const cb = num("cb"), m = num("moisture"), gcs = num("gcs"), initWt = num("init_wt", 50);
  const sieves = SIEVES.map((_, i) => num(`sieve_${i}`));

  const denom = 660.5 - 5.0 * cb;
  const wb = (gcs > 0 && denom !== 0) ? (110.8 * gcs) / denom : 0;
  const ab = (m > 0 || gcs > 0) ? (1.316 * m + 0.1527 * gcs) : 0;
  const me = ab > 0 ? (wb / ab) * 100 : 0;

  const totalRet = sieves.reduce((a, b) => a + b, 0);
  let clay = 0, gfn = 0, pcts = new Array(12).fill(0);
  if (initWt > 0 && totalRet > 0) {
    clay = ((initWt - totalRet) / initWt) * 100;
    pcts = sieves.map(w => (w / totalRet) * 100);
    gfn = pcts.reduce((acc, p, i) => acc + p * SIEVES[i][2], 0) / 100;
  }
  return {
    cb, m, density: num("density"), perm: num("perm"), shear: num("shear"),
    gcs, cb_wt: num("cb_wt"), dcs: num("dcs"), wts: num("wts"),
    mb_clay: num("mb_clay"), vm: num("vm"), loi: num("loi"),
    wb, ab, me, clay, gfn, pcts, totalRet
  };
}

function loadRecordToForm(idx) {
  const recs = curCompany().records;
  selectedIdx = idx;
  const rec = recs[idx];
  document.getElementById("form_title").textContent =
    `1. 측정 데이터 입력 (${idx + 1}열 - ${idx < 8 ? "최근 8건 포함" : "백데이터 보관분"})`;

  BASIC_FIELDS.forEach(([key]) => {
    document.getElementById(`inp_${key}`).value = rec[key] ?? "";
  });
  SIEVES.forEach((_, i) => {
    document.getElementById(`inp_sieve_${i}`).value = rec[`sieve_${i}`] ?? "0.0";
  });
  updateCalcAndTable();
}

function updateCalcAndTable() {
  const comp = curCompany();
  const recs = comp.records;
  const totalCount = recs.length;
  const showAll = document.getElementById("chk_show_all").checked;
  const visibleList = showAll ? recs : recs.slice(0, 8);

  document.getElementById("badge_total").textContent =
    `[${comp.meta.customer}] 백데이터 누적: 총 ${totalCount}건 (성적서 표시: 최근 ${Math.min(8, totalCount)}건)`;
  document.getElementById("hist_heading").textContent =
    showAll ? `3. 전체 백데이터 이력 (총 ${totalCount}건 / 맨 위 1열이 최신)` : `3. 최근 8개 시험 이력 (전체 ${totalCount}건 중 최근 ${visibleList.length}건 표시)`;

  const cur = recs[selectedIdx];
  const res = compute(cur);
  document.getElementById("kpi_wb").textContent = res.wb.toFixed(2);
  document.getElementById("kpi_ab").textContent = res.ab.toFixed(2);
  document.getElementById("kpi_me").textContent = res.me.toFixed(1) + " %";
  document.getElementById("kpi_clay").textContent = res.clay.toFixed(2) + " %";
  document.getElementById("kpi_gfn").textContent = res.gfn.toFixed(2);

  if (res.totalRet > 0) {
    const parts = res.pcts
      .map((p, i) => p > 0.05 ? `${SIEVES[i][1]}: ${p.toFixed(1)}%` : null)
      .filter(Boolean);
    document.getElementById("sieve_pct_bar").textContent = "체가름 잔류율(%):  " + parts.join("  |  ");
  } else {
    document.getElementById("sieve_pct_bar").textContent = "체가름 잔류율(%):  (체가름 무게를 입력하면 자동 계산됩니다)";
  }

  const tbody = document.getElementById("hist_tbody");
  tbody.innerHTML = "";
  visibleList.forEach((rec, i) => {
    const c = compute(rec);
    const tr = document.createElement("tr");
    if (i === selectedIdx) tr.className = "active";
    tr.onclick = () => loadRecordToForm(i);
    tr.innerHTML = `
      <td>${i + 1}열${i === 0 ? " (최신)" : ""}</td>
      <td>${rec.confirm_date || "-"}</td>
      <td>${rec.cs_no || "-"}</td>
      <td>${rec.cb || "-"}</td>
      <td>${rec.moisture || "-"}</td>
      <td>${rec.gcs || "-"}</td>
      <td>${c.wb > 0 ? c.wb.toFixed(2) : "-"}</td>
      <td>${c.ab > 0 ? c.ab.toFixed(2) : "-"}</td>
      <td>${c.me > 0 ? c.me.toFixed(1) : "-"}</td>
      <td>${c.clay > 0 ? c.clay.toFixed(2) : "-"}</td>
      <td>${c.gfn > 0 ? c.gfn.toFixed(2) : "-"}</td>
    `;
    tbody.appendChild(tr);
  });
}

function insertShiftColumn() {
  const d = document.getElementById("report_date").value || todayStr();
  document.getElementById("report_date").value = d;
  const newRec = {
    confirm_date: d,
    request_date: d,
    cs_no: "DKY-" + d.slice(5).replace("-", ""),
    cb: "", moisture: "", density: "", perm: "", shear: "", gcs: "",
    cb_wt: "", dcs: "", wts: "", init_wt: "50.0", mb_clay: "", vm: "", loi: ""
  };
  for (let i = 0; i < 12; i++) newRec[`sieve_${i}`] = "0.0";
  curCompany().records.unshift(newRec);
  renderCompanyDropdown();
  loadRecordToForm(0);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast(`[${curCompany().meta.customer}] ${d} 기준 새 1열이 생성되었습니다.`);
}

function cancelInput() {
  const currentStr = JSON.stringify(rootDB);
  if (currentStr === savedSnapshot) {
    showToast("변경된 입력 내용이 없습니다.");
    return;
  }

  const firstCheck = confirm(
    "[더블체크] 현재 입력/수정 중인 내용을 모두 취소하고 마지막 저장 상태로 되돌리시겠습니까?\n\n※ 아직 저장하지 않은 입력 내용 및 신규 추가된 열이 모두 원래대로 복구됩니다."
  );
  if (!firstCheck) return;

  rootDB = JSON.parse(savedSnapshot);
  applyMetaToInputs();
  renderCompanyDropdown();
  const recs = curCompany().records;
  const safeIdx = Math.min(selectedIdx, recs.length - 1);
  loadRecordToForm(Math.max(0, safeIdx));
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast("입력이 취소되고 마지막 저장 상태로 복구되었습니다.");
}

function deleteSelected() {
  const recs = curCompany().records;
  if (recs.length <= 1) {
    alert("최소 1개의 데이터 열은 유지되어야 합니다.");
    return;
  }
  if (!confirm(`[더블체크] ${selectedIdx + 1}열 데이터를 정말 삭제하시겠습니까?`)) return;
  recs.splice(selectedIdx, 1);
  renderCompanyDropdown();
  loadRecordToForm(Math.min(selectedIdx, recs.length - 1));
  saveAll(true);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast("선택한 열이 삭제되었습니다.");
}

async function saveAll(silent=false) {
  syncMeta();
  const payload = JSON.stringify(rootDB);
  await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload
  });
  savedSnapshot = payload;
  renderCompanyDropdown();
  if (!silent) {
    const comp = curCompany();
    showToast(`[${comp.meta.customer}] 전체 백데이터(${comp.records.length}건)가 저장되었습니다.`);
  }
}

async function handleImportFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company_id", rootDB.active_id);

  const res = await fetch("/api/import", { method: "POST", body: formData });
  const result = await res.json();
  event.target.value = "";

  if (!result.ok) {
    alert("파일 불러오기 실패:\n" + result.error);
    return;
  }
  rootDB = result.data;
  savedSnapshot = JSON.stringify(rootDB);
  applyMetaToInputs();
  renderCompanyDropdown();
  loadRecordToForm(0);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  showToast(`[${curCompany().meta.customer}] 총 ${curCompany().records.length}건의 백데이터를 불러왔습니다!`);
}

async function handleBulkImportFiles(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const res = await fetch("/api/bulk_import", { method: "POST", body: formData });
  const result = await res.json();
  event.target.value = "";

  if (!result.ok) {
    alert("일괄 불러오기 실패:\n" + result.error);
    return;
  }
  rootDB = result.data;
  savedSnapshot = JSON.stringify(rootDB);
  applyMetaToInputs();
  renderCompanyDropdown();
  loadRecordToForm(0);
  if (document.getElementById("view_report").style.display === "flex") renderReportPages();
  alert(`일괄 불러오기 완료!\n\n${result.summary}`);
}

function buildReportHeaderHTML(telSeparator) {
  const m = curCompany().meta;
  const rDate = fmtDotDate(m.report_date || todayStr());
  return `
    <div class="rep-header">
      <div class="rep-header-left">
        <div>수신: &nbsp;<span class="cust">${m.customer || ""}</span></div>
        <div style="padding-left: 34px;">
          <div>${m.address || ""}</div>
          <div>Tel: ${m.tel || "041-337-7250~2"}${telSeparator}Fax: ${m.fax || "041-338-3686"}</div>
          <div class="line-name">${m.line || ""}</div>
        </div>
      </div>
      <div class="rep-header-right">
        <table>
          <tr><td style="font-weight:700;">Date:</td><td style="font-weight:700;">${rDate}</td></tr>
          <tr><td colspan="2" style="height:6px;"></td></tr>
          <tr><td style="font-weight:700;">Copy:</td><td>${m.person || ""}</td></tr>
          <tr><td></td><td>${m.copy || ""}</td></tr>
        </table>
      </div>
    </div>
  `;
}

function renderReportPages() {
  const recentRaw = curCompany().records.slice(0, 8).reverse();
  const cols = [...recentRaw];
  while (cols.length < 8) cols.push(null);
  const calcs = cols.map(r => compute(r));

  const fmtCell = (c, fn) => (c ? fn(c) : "");

  // --- [PAGE 1: 시험 성적표] ---
  let p1 = buildReportHeaderHTML("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
  p1 += `<table class="rep-table">`;

  p1 += `<tr class="top-border"><td class="label-col">Confirmation date to Customers</td>`;
  cols.forEach(r => p1 += `<td class="head-val">${r ? fmtShortDate(r.confirm_date) : ""}</td>`);
  p1 += `</tr>`;

  p1 += `<tr><td class="label-col">Request date from Customers</td>`;
  cols.forEach(r => p1 += `<td class="head-val">${r ? fmtShortDate(r.request_date) : ""}</td>`);
  p1 += `</tr>`;

  p1 += `<tr class="bottom-border"><td class="label-col">Customer Service No.</td>`;
  cols.forEach(r => p1 += `<td class="head-val">${r ? (r.cs_no || "") : ""}</td>`);
  p1 += `</tr>`;

  p1 += `<tr class="section-banner"><td colspan="9">GREEN PROPERTIES (USING AFS STANDARD 2" x 2" SPECIMEN)</td></tr>`;

  const greenRows = [
    ["충진도, Compactability (%)", c => c.cb ? c.cb.toFixed(0) : ""],
    ["수분, Moisture (% by wt)", c => c.m ? c.m.toFixed(1) : ""],
    ['시편무게, Density (g/2" x 2" specimen)', c => c.density ? c.density.toFixed(0) : ""],
    ["통기도, Permeability No.", c => c.perm ? c.perm.toFixed(0) : ""],
    ["전단강도, Shear Strength (N/sq.cm)", c => c.shear ? c.shear.toFixed(1) : ""],
    ["생형압축강도, Green Comp. Str. (N/sq.cm)", c => c.gcs ? c.gcs.toFixed(1) : ""],
    ["실용점토분, Working Bond", c => c.wb ? c.wb.toFixed(1) : ""],
    ["유효점토분, Available Bond", c => c.ab ? c.ab.toFixed(1) : ""],
    ["믹싱효율, Muller Effectiveness (%)", c => c.me ? c.me.toFixed(0) : ""],
    ["충진도시편무게, Weight of CB Specimen (g)", c => c.cb_wt ? c.cb_wt.toFixed(1) : ""]
  ];
  greenRows.forEach(([lbl, fn], idx) => {
    const cls = idx === greenRows.length - 1 ? ' class="bottom-border"' : "";
    p1 += `<tr${cls}><td class="label-col">${lbl}</td>`;
    calcs.forEach(c => p1 += `<td class="val-col">${fmtCell(c, fn)}</td>`);
    p1 += `</tr>`;
  });

  p1 += `<tr class="section-banner"><td colspan="9">DRY COMPRESSION STRENGTH (USING AFS STANDARD 2" x 2" SPECIMEN)</td></tr>`;
  p1 += `<tr><td class="label-col">건태강도, Dry Compression Str. (N/sq.cm)</td>`;
  calcs.forEach(c => p1 += `<td class="val-col">${fmtCell(c, x => x.dcs ? x.dcs.toFixed(0) : "")}</td>`);
  p1 += `</tr>`;
  p1 += `<tr class="bottom-border"><td class="label-col">습태인장강도, Wet Tensile Str. (N/sq.cm)</td>`;
  calcs.forEach(c => p1 += `<td class="val-col">${fmtCell(c, x => x.wts ? x.wts.toFixed(3) : "")}</td>`);
  p1 += `</tr>`;

  p1 += `<tr class="section-banner"><td colspan="9">SIEVE ANALYSIS, AFS CLAY CONTENT AND LOSS ON IGNITION</td></tr>`;
  p1 += `<tr><td class="label-col" style="padding:1px 4px;">
    <table class="sieve-subtable"><tr><td style="width:62px;">USA</td><td colspan="2" style="text-align:center;">Series Designation</td></tr></table>
  </td>` + `<td></td>`.repeat(8) + `</tr>`;
  p1 += `<tr><td class="label-col" style="padding:1px 4px;">
    <table class="sieve-subtable"><tr><td style="width:62px;"></td><td style="width:68px; text-align:right;">Standard</td><td style="text-align:right; padding-right:10px;">Alternate</td></tr></table>
  </td>` + `<td></td>`.repeat(8) + `</tr>`;

  const leftWords = ["Percent", "Retained", "on", "USA Std.", "Sieves", "with ASTM", "Specification", "E-11-70", "and", "I.S.O.", "", ""];
  SIEVES.forEach(([stdN, altN], sIdx) => {
    const cls = sIdx === SIEVES.length - 1 ? ' class="bottom-border"' : "";
    p1 += `<tr${cls}><td class="label-col" style="padding:0 4px;">
      <table class="sieve-subtable">
        <tr>
          <td style="width:66px;">${leftWords[sIdx]}</td>
          <td style="width:64px; text-align:right;">${stdN}</td>
          <td style="text-align:right; padding-right:12px;">${altN}</td>
        </tr>
      </table>
    </td>`;
    calcs.forEach(c => p1 += `<td class="val-col">${c && c.totalRet > 0 ? c.pcts[sIdx].toFixed(1) : ""}</td>`);
    p1 += `</tr>`;
  });

  const bottomRows = [
    ["전점토분, AFS Clay Content (% <20 µm)", c => c.totalRet > 0 ? c.clay.toFixed(1) : ""],
    ["입도지수, AFS Grain Fineness No.", c => c.totalRet > 0 ? c.gfn.toFixed(0) : ""],
    ["활성점토분, Percent M.B. Active Clay", c => c.mb_clay ? c.mb_clay.toFixed(1) : ""],
    ["휘발분, V. Combustile M. @649°C (%)", c => c.vm ? c.vm.toFixed(1) : ""],
    ["작열감량, Loss on Ignition @1010 °C (%)", c => c.loi ? c.loi.toFixed(1) : ""]
  ];
  bottomRows.forEach(([lbl, fn], idx) => {
    const cls = idx === bottomRows.length - 1 ? ' class="bottom-border"' : "";
    p1 += `<tr${cls}><td class="label-col">${lbl}</td>`;
    calcs.forEach(c => p1 += `<td class="val-col">${fmtCell(c, fn)}</td>`);
    p1 += `</tr>`;
  });

  p1 += `</table>`;
  document.getElementById("report_page_1").innerHTML = p1;

  // --- [PAGE 2: 8대 핵심 물성 추이 그래프] ---
  let p2 = buildReportHeaderHTML(" ");
  p2 += `<div class="charts-grid">`;

  const chartSpecs = [
    { title: "MOISTURE CONTENT", yLabel: "% by wt", min: 3.0, max: 6.0, step: 0.5, dec: 1, type: "diamond", getVal: c => c.m },
    { title: "COMPACTABILITY", yLabel: "%", min: 20, max: 50, step: 5, dec: 0, type: "diamond", getVal: c => c.cb },
    { title: "GREEN COMPRESSION STRENGTH", yLabel: "N/sqcm", min: 10.0, max: 30.0, step: 5.0, dec: 1, type: "diamond", getVal: c => c.gcs },
    { title: "PERMEABILITY", yLabel: "", min: 90, max: 210, step: 20, dec: 0, type: "diamond", getVal: c => c.perm },
    { title: "AFS CLAY CONTENT", yLabel: "% by wt.", min: 8.0, max: 20.0, step: 2.0, dec: 1, type: "diamond", getVal: c => c.totalRet > 0 ? c.clay : 0 },
    { title: "LOI", yLabel: "% by wt.", min: 3, max: 6, step: 0.5, dec: 1, type: "square", legend: "L.O.I.", getVal: c => c.loi },
    { title: "MULLER EFFECTIVENESS", yLabel: "%", min: 30, max: 80, step: 10, dec: 0, type: "diamond", getVal: c => c.me },
    { title: "METHYLENE BLUE ACTIVE CLAY", yLabel: "%", min: 6.0, max: 16.0, step: 1.0, dec: 1, type: "diamond", getVal: c => c.mb_clay }
  ];

  chartSpecs.forEach(spec => {
    p2 += `<div class="chart-cell">
      <div class="chart-title">${spec.title}</div>
      ${renderChartSVG(spec, cols, calcs)}
    </div>`;
  });

  p2 += `</div>`;
  document.getElementById("report_page_2").innerHTML = p2;
}

function renderChartSVG(spec, cols, calcs) {
  const W = 330, H = 175;
  const padL = 44, padR = 14, padT = 14, padB = spec.legend ? 42 : 32;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;

  if (spec.yLabel) {
    svg += `<text x="12" y="${padT + plotH / 2}" font-size="9.5" font-weight="700" text-anchor="middle" transform="rotate(-90, 12, ${padT + plotH / 2})">${spec.yLabel}</text>`;
  }

  svg += `<line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + plotH}" stroke="#000" stroke-width="1"/>`;
  svg += `<line x1="${padL}" y1="${padT + plotH}" x2="${padL + plotW}" y2="${padT + plotH}" stroke="#000" stroke-width="1"/>`;

  const steps = Math.round((spec.max - spec.min) / spec.step);
  for (let s = 0; s <= steps; s++) {
    const val = spec.min + s * spec.step;
    const y = padT + plotH - ((val - spec.min) / (spec.max - spec.min)) * plotH;
    svg += `<line x1="${padL}" y1="${y}" x2="${padL + 3.5}" y2="${y}" stroke="#000" stroke-width="1"/>`;
    svg += `<text x="${padL - 5}" y="${y + 3}" font-size="9" text-anchor="end">${val.toFixed(spec.dec)}</text>`;
  }

  const pts = [];
  for (let i = 0; i < 8; i++) {
    const x = padL + ((i + 0.5) / 8) * plotW;
    const tickX = padL + ((i + 1) / 8) * plotW;
    svg += `<line x1="${tickX}" y1="${padT + plotH}" x2="${tickX}" y2="${padT + plotH - 3.5}" stroke="#000" stroke-width="1"/>`;

    const r = cols[i];
    const c = calcs[i];
    if (r && r.cs_no) {
      const parts = r.cs_no.split("-");
      if (parts.length === 2) {
        svg += `<text x="${x}" y="${padT + plotH + 12}" font-size="8.5" text-anchor="middle">${parts[0]}-</text>`;
        svg += `<text x="${x}" y="${padT + plotH + 22}" font-size="8.5" text-anchor="middle">${parts[1]}</text>`;
      } else {
        svg += `<text x="${x}" y="${padT + plotH + 14}" font-size="8.5" text-anchor="middle">${r.cs_no}</text>`;
      }
    }

    if (c) {
      const v = spec.getVal(c);
      if (v > 0) {
        const clamped = Math.max(spec.min, Math.min(spec.max, v));
        const y = padT + plotH - ((clamped - spec.min) / (spec.max - spec.min)) * plotH;
        pts.push({ x, y });
      }
    }
  }

  const strokeColor = spec.type === "square" ? "#000000" : "#000080";
  if (pts.length > 1) {
    const dStr = pts.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
    svg += `<path d="${dStr}" fill="none" stroke="${strokeColor}" stroke-width="1.2"/>`;
  }

  pts.forEach(p => {
    if (spec.type === "square") {
      svg += `<rect x="${p.x - 2.6}" y="${p.y - 2.6}" width="5.2" height="5.2" fill="#000"/>`;
    } else {
      svg += `<polygon points="${p.x},${p.y - 3.6} ${p.x + 3.6},${p.y} ${p.x},${p.y + 3.6} ${p.x - 3.6},${p.y}" fill="#000080"/>`;
    }
  });

  if (spec.legend) {
    const ly = H - 6;
    const lx = W / 2 - 20;
    svg += `<line x1="${lx}" y1="${ly}" x2="${lx + 18}" y2="${ly}" stroke="#000" stroke-width="1"/>`;
    svg += `<rect x="${lx + 6.5}" y="${ly - 2.5}" width="5" height="5" fill="#000"/>`;
    svg += `<text x="${lx + 22}" y="${ly + 3}" font-size="8.5">${spec.legend}</text>`;
  }

  svg += `</svg>`;
  return svg;
}

async function init() {
  buildForms();
  const res = await fetch("/api/load");
  rootDB = await res.json();
  const comp = curCompany();
  comp.meta.report_date = todayStr();
  applyMetaToInputs();
  renderCompanyDropdown();
  savedSnapshot = JSON.stringify(rootDB);
  loadRecordToForm(0);
}

init();
</script>
</body>
</html>
"""


def get_initial_data():
    today_s = date.today().strftime("%Y-%m-%d")
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if "companies" not in raw and "records" in raw:
                migrated = {
                    "active_id": "comp_default",
                    "companies": {
                        "comp_default": {
                            "meta": raw.get("meta", {
                                "customer": "대광주철(주)",
                                "address": "충청남도 예산군 고덕면 상몽2길",
                                "tel": "041-337-7250~2",
                                "fax": "041-338-3686",
                                "line": "DISA_CH line",
                                "person": "최재호상무님",
                                "copy": "서순조고문",
                                "report_date": today_s,
                            }),
                            "records": raw.get("records", []),
                        }
                    },
                }
                with open(DB_FILE, "w", encoding="utf-8") as wf:
                    json.dump(migrated, wf, ensure_ascii=False, indent=2)
                return migrated
            if "companies" in raw and raw["companies"]:
                if raw.get("active_id") not in raw["companies"]:
                    raw["active_id"] = next(iter(raw["companies"].keys()))
                return raw
        except Exception:
            pass

    return {
        "active_id": "comp_default",
        "companies": {
            "comp_default": {
                "meta": {
                    "customer": "대광주철(주)",
                    "address": "충청남도 예산군 고덕면 상몽2길",
                    "tel": "041-337-7250~2",
                    "fax": "041-338-3686",
                    "line": "DISA_CH line",
                    "person": "최재호상무님",
                    "copy": "서순조고문",
                    "report_date": today_s,
                },
                "records": [
                    {
                        "confirm_date": today_s,
                        "request_date": today_s,
                        "cs_no": "DKY-" + date.today().strftime("%m%d"),
                        "cb": "34", "moisture": "4.60", "density": "148", "perm": "152",
                        "shear": "5.0", "gcs": "20.0", "cb_wt": "219.1", "dcs": "50",
                        "wts": "0.353", "init_wt": "50.0",
                        "sieve_0": "0.0", "sieve_1": "0.0", "sieve_2": "0.15", "sieve_3": "0.46",
                        "sieve_4": "1.68", "sieve_5": "7.75", "sieve_6": "17.20", "sieve_7": "11.72",
                        "sieve_8": "2.29", "sieve_9": "0.61", "sieve_10": "0.24", "sieve_11": "0.39",
                        "mb_clay": "12.0", "vm": "1.88", "loi": "3.90",
                    }
                ],
            }
        },
    }


def extract_rows_from_file(filename, file_bytes):
    if filename.lower().endswith(".csv"):
        text = file_bytes.decode("utf-8-sig", errors="replace")
        return list(csv.reader(text.splitlines()))
    elif filename.lower().endswith(".xlsx"):
        import openpyxl
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
        sh = wb["시험결과"] if "시험결과" in wb.sheetnames else wb.active
        return [[cell.value for cell in row] for row in sh.iter_rows()]
    elif filename.lower().endswith(".xls"):
        import xlrd
        wb = xlrd.open_workbook(file_contents=file_bytes)
        sh = wb.sheet_by_name("시험결과") if "시험결과" in wb.sheet_names() else wb.sheet_by_index(0)
        rows = []
        for r in range(sh.nrows):
            r_vals = []
            for c in range(sh.ncols):
                val = sh.cell_value(r, c)
                if sh.cell_type(r, c) == xlrd.XL_CELL_DATE:
                    dt = xlrd.xldate_as_datetime(val, wb.datemode)
                    r_vals.append(dt.strftime("%Y-%m-%d"))
                else:
                    r_vals.append(val)
            rows.append(r_vals)
        return rows
    else:
        raise ValueError(f"[{filename}] .csv, .xls, .xlsx 파일만 지원합니다.")


def parse_sheet_to_company_obj(rows, fallback_name=""):
    cs_row_idx = None
    for r_idx, row in enumerate(rows):
        row_str = " ".join(str(c or "") for c in row)
        if "Customer Service No" in row_str or "DKY-" in row_str:
            cs_row_idx = r_idx
            break

    if cs_row_idx is None:
        raise ValueError("시트에서 'Customer Service No.' 또는 'DKY-' 행을 찾을 수 없습니다.")

    records = []
    max_cols = max(len(r) for r in rows)

    def cell(r, c):
        if r < 0 or r >= len(rows) or c >= len(rows[r]):
            return ""
        val = rows[r][c]
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, float):
            return str(int(val)) if val.is_integer() else str(round(val, 4))
        return str(val or "").strip()

    for c in range(max_cols):
        cs_val = cell(cs_row_idx, c)
        c_date = cell(cs_row_idx - 2, c)
        if not cs_val and not (len(c_date) >= 8 and "-" in c_date):
            continue
        if "Customer Service" in cs_val or "Confirmation" in c_date or c < 2:
            continue

        def norm_date(d_str):
            if not d_str:
                return ""
            parts = d_str.split("-")
            if len(parts) == 3 and parts[0].isdigit():
                y = parts[0] if len(parts[0]) == 4 else f"20{parts[0]}"
                return f"{y}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            return d_str

        sieve_start = cs_row_idx + 12
        for probe in range(cs_row_idx + 10, min(len(rows), cs_row_idx + 16)):
            lbl_probe = " ".join(cell(probe, k) for k in range(min(4, max_cols)))
            if "3.35" in lbl_probe or "No. 6" in lbl_probe:
                sieve_start = probe
                break

        rec = {
            "confirm_date": norm_date(c_date),
            "request_date": norm_date(cell(cs_row_idx - 1, c)),
            "cs_no": cs_val,
            "cb": cell(cs_row_idx + 1, c),
            "moisture": cell(cs_row_idx + 2, c),
            "density": cell(cs_row_idx + 3, c),
            "perm": cell(cs_row_idx + 4, c),
            "shear": cell(cs_row_idx + 5, c),
            "gcs": cell(cs_row_idx + 6, c),
            "cb_wt": cell(cs_row_idx + 7, c),
            "dcs": cell(cs_row_idx + 8, c),
            "wts": cell(cs_row_idx + 9, c),
            "init_wt": cell(cs_row_idx + 10, c) or "50.0",
            "mb_clay": cell(sieve_start + 12, c),
            "vm": cell(sieve_start + 13, c),
            "loi": cell(sieve_start + 14, c),
        }
        for s_i in range(12):
            rec[f"sieve_{s_i}"] = cell(sieve_start + s_i, c) or "0.0"

        records.append(rec)

    if not records:
        raise ValueError("추출된 시험 데이터 열이 없습니다.")

    sheet_cust = cell(0, 1) or fallback_name
    sheet_addr = cell(1, 1)
    sheet_line = cell(4, 1)
    sheet_person = cell(6, 1)
    sheet_copy = cell(7, 1)

    return {
        "meta": {
            "customer": sheet_cust,
            "address": sheet_addr,
            "tel": "041-337-7250~2",
            "fax": "041-338-3686",
            "line": sheet_line,
            "person": sheet_person,
            "copy": sheet_copy,
            "report_date": date.today().strftime("%Y-%m-%d"),
        },
        "records": records,
    }


def parse_multipart(headers, raw_body):
    content_type = headers.get("Content-Type", "")
    boundary = content_type.split("boundary=")[-1].encode("utf-8")
    parts = raw_body.split(b"--" + boundary)
    fields = {}
    files = []
    for p in parts:
        if b"Content-Disposition:" not in p:
            continue
        header_part, body_part = p.split(b"\r\n\r\n", 1)
        body_part = body_part.rstrip(b"\r\n--")
        header_str = header_part.decode("utf-8", errors="ignore")
        name_m = re.search(r'name="([^"]+)"', header_str)
        file_m = re.search(r'filename="([^"]+)"', header_str)
        if file_m:
            files.append((file_m.group(1), body_part))
        elif name_m:
            fields[name_m.group(1)] = body_part.decode("utf-8", errors="ignore").strip()
    return fields, files


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/load":
            data = get_initial_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/ping":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"pong")

    def do_POST(self):
        if self.path == "/api/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            with open(DB_FILE, "w", encoding="utf-8") as f:
                f.write(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        elif self.path == "/api/shutdown":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        elif self.path == "/api/import":
            try:
                length = int(self.headers.get("Content-Length", 0))
                fields, files = parse_multipart(self.headers, self.rfile.read(length))
                if not files:
                    raise ValueError("업로드된 파일 데이터를 읽지 못했습니다.")

                filename, file_bytes = files[0]
                company_id = fields.get("company_id", "")
                rows = extract_rows_from_file(filename, file_bytes)
                parsed = parse_sheet_to_company_obj(rows, os.path.splitext(filename)[0])

                cur_db = get_initial_data()
                target_id = company_id if company_id in cur_db["companies"] else cur_db["active_id"]
                cur_db["active_id"] = target_id

                old_meta = cur_db["companies"][target_id]["meta"]
                for k, v in parsed["meta"].items():
                    if v:
                        old_meta[k] = v
                cur_db["companies"][target_id]["records"] = parsed["records"]

                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(cur_db, f, ensure_ascii=False, indent=2)

                resp = json.dumps({"ok": True, "data": cur_db}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(resp)

        elif self.path == "/api/bulk_import":
            try:
                length = int(self.headers.get("Content-Length", 0))
                _, files = parse_multipart(self.headers, self.rfile.read(length))
                if not files:
                    raise ValueError("선택된 파일이 없습니다.")

                cur_db = get_initial_data()
                summary_lines = []
                last_id = cur_db["active_id"]

                for idx, (filename, file_bytes) in enumerate(files):
                    rows = extract_rows_from_file(filename, file_bytes)
                    fallback = os.path.splitext(filename)[0]
                    parsed = parse_sheet_to_company_obj(rows, fallback)
                    cust = parsed["meta"]["customer"]
                    line = parsed["meta"]["line"]

                    matched_id = None
                    for cid, cobj in cur_db["companies"].items():
                        if cobj["meta"].get("customer") == cust and cobj["meta"].get("line") == line:
                            matched_id = cid
                            break

                    if matched_id:
                        cur_db["companies"][matched_id] = parsed
                        last_id = matched_id
                    else:
                        new_id = f"comp_{int(datetime.now().timestamp() * 1000)}_{idx}"
                        cur_db["companies"][new_id] = parsed
                        last_id = new_id

                    summary_lines.append(f"• {cust} ({line or '라인미지정'}): {len(parsed['records'])}건")

                cur_db["active_id"] = last_id
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(cur_db, f, ensure_ascii=False, indent=2)

                resp = json.dumps({
                    "ok": True,
                    "data": cur_db,
                    "summary": "\n".join(summary_lines)
                }, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(resp)


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    # 이미 프로그램이 실행 중이면 중복 실행하지 않고 브라우저 새 탭만 열기
    try:
        urllib.request.urlopen(f"{url}/api/ping", timeout=0.5)
        webbrowser.open(url)
        sys.exit(0)
    except Exception:
        pass

    server = HTTPServer(("127.0.0.1", PORT), AppHandler)
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    server.serve_forever()