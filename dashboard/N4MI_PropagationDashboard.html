<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>N4MI Propagation Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;600;800&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #090d12;
    --panel:    #0d1520;
    --border:   #1a2d45;
    --accent:   #00d4ff;
    --accent2:  #ff6b35;
    --text:     #c8dce8;
    --muted:    #4a6a80;
    --good:     #39ff14;
    --fair:     #ffd700;
    --poor:     #ff4444;
    --band80:   #ff6b6b;
    --band40:   #ffa500;
    --band20:   #39ff14;
    --band17:   #00d4ff;
    --band15:   #a78bfa;
    --band12:   #f472b6;
    --band10:   #fb923c;
    --band6:    #facc15;
  }

  * { margin:0; padding:0; box-sizing:border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    min-height: 100vh;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,212,255,0.012) 2px,rgba(0,212,255,0.012) 4px);
    pointer-events: none;
    z-index: 9999;
  }

  /* ── Header ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
  }
  .callsign {
    font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 800;
    color: var(--accent); letter-spacing: 4px;
    text-shadow: 0 0 20px rgba(0,212,255,0.5);
  }
  .callsign span { color: var(--accent2); font-size: 12px; font-weight: 400; letter-spacing: 2px; display: block; margin-top: 2px; }
  .header-right { display: flex; align-items: center; gap: 20px; }
  .utc-clock { font-family: 'Share Tech Mono', monospace; font-size: 20px; color: var(--accent); text-shadow: 0 0 12px rgba(0,212,255,0.4); }
  .utc-label { font-size: 10px; color: var(--muted); letter-spacing: 2px; text-align: right; margin-top: 2px; }
  .refresh-btn {
    background: transparent; border: 1px solid var(--accent); color: var(--accent);
    font-family: 'Share Tech Mono', monospace; font-size: 11px; padding: 6px 14px;
    cursor: pointer; letter-spacing: 1px; transition: all 0.2s;
  }
  .refresh-btn:hover { background: var(--accent); color: var(--bg); }

  /* ── Solar bar ── */
  .solar-bar {
    display: flex; background: var(--panel);
    border-bottom: 1px solid var(--border); padding: 0 24px;
  }
  .solar-item {
    padding: 10px 20px 10px 0; margin-right: 20px;
    border-right: 1px solid var(--border);
  }
  .solar-item:last-child { border-right: none; margin-left: auto; }
  .solar-label { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: var(--muted); letter-spacing: 1px; }
  .solar-value { font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 600; }
  .solar-sub   { font-size: 9px; color: var(--muted); margin-top: 1px; }

  /* ── Main layout ── */
  /* Row 1: band conditions | MUF map | cluster links  (3 cols) */
  /* Row 2: DX cluster iframe (full width) */
  .main {
    display: grid;
    grid-template-columns: 320px 1fr 260px;
    grid-template-rows: auto auto;
    gap: 1px;
    background: var(--border);
  }

  .panel {
    background: var(--panel); padding: 14px; position: relative; overflow: hidden;
  }

  .panel-title {
    font-family: 'Orbitron', monospace; font-size: 10px; font-weight: 600;
    color: var(--accent); letter-spacing: 3px; margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .panel-title::before {
    content: ''; display: inline-block; width: 6px; height: 6px;
    background: var(--accent); box-shadow: 0 0 6px var(--accent);
    animation: blink 2s infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

  /* ── Band conditions ── */
  .band-panel { grid-column: 1; grid-row: 1; }

  .status-row { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }
  .status-pill {
    font-family: 'Share Tech Mono', monospace; font-size: 9px;
    padding: 2px 8px; border: 1px solid; letter-spacing: 1px;
  }
  .status-pill.good { color:var(--good);  border-color:var(--good);  background:rgba(57,255,20,0.08); }
  .status-pill.fair { color:var(--fair);  border-color:var(--fair);  background:rgba(255,215,0,0.08); }
  .status-pill.poor { color:var(--poor);  border-color:var(--poor);  background:rgba(255,68,68,0.08); }

  .band-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

  .band-card {
    border: 1px solid var(--border); padding: 8px 10px;
    position: relative; overflow: hidden; cursor: default;
    transition: border-color 0.2s;
  }
  .band-card:hover { border-color: var(--accent); }
  .band-card::before { content:''; position:absolute; left:0;top:0;bottom:0; width:3px; }

  .band-card.b80::before{background:var(--band80)} .band-card.b40::before{background:var(--band40)}
  .band-card.b20::before{background:var(--band20)} .band-card.b17::before{background:var(--band17)}
  .band-card.b15::before{background:var(--band15)} .band-card.b12::before{background:var(--band12)}
  .band-card.b10::before{background:var(--band10)} .band-card.b6::before {background:var(--band6)}

  .band-name { font-family:'Orbitron',monospace; font-size:13px; font-weight:600; margin-left:6px; }
  .band-card.b80 .band-name{color:var(--band80)} .band-card.b40 .band-name{color:var(--band40)}
  .band-card.b20 .band-name{color:var(--band20)} .band-card.b17 .band-name{color:var(--band17)}
  .band-card.b15 .band-name{color:var(--band15)} .band-card.b12 .band-name{color:var(--band12)}
  .band-card.b10 .band-name{color:var(--band10)} .band-card.b6  .band-name{color:var(--band6)}

  .band-status { font-family:'Share Tech Mono',monospace; font-size:11px; margin-left:6px; margin-top:3px; }
  .band-status.good { color:var(--good); }
  .band-status.fair { color:var(--fair); }
  .band-status.poor { color:var(--poor); }
  .band-detail { font-size:9px; color:var(--muted); margin-left:6px; margin-top:2px; }
  .data-note { font-size:9px; color:var(--muted); margin-top:8px; font-style:italic; }

  /* ── MUF Map (center) ── */
  .map-panel { grid-column: 2; grid-row: 1; display: flex; flex-direction: column; min-height: 420px; }
  .map-container { flex:1; position:relative; min-height:360px; }
  .map-container iframe { width:100%; height:100%; border:none; min-height:360px; filter:brightness(0.9) saturate(1.1); }

  /* ── Cluster links panel ── */
  .links-panel { grid-column: 3; grid-row: 1; }
  .cluster-link {
    display: block; text-align: left; padding: 9px 12px; margin-bottom: 5px;
    border: 1px solid var(--border); color: var(--accent);
    font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 1px;
    text-decoration: none; transition: all 0.2s;
  }
  .cluster-link:hover { background: var(--accent); color: var(--bg); border-color: var(--accent); }
  .cluster-link.accent2 { color: var(--accent2); border-color: var(--border); }
  .cluster-link.accent2:hover { background: var(--accent2); color: var(--bg); border-color: var(--accent2); }
  .link-section-label {
    font-family: 'Share Tech Mono', monospace; font-size: 9px;
    color: var(--muted); letter-spacing: 2px; margin: 10px 0 5px;
  }

  /* ── DX Cluster iframe row ── */
  .spots-panel { grid-column: 1 / 4; grid-row: 2; min-height: 480px; display: flex; flex-direction: column; }
  .spots-tabs { display: flex; gap: 1px; margin-bottom: 0; }
  .spots-tab {
    font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 1px;
    padding: 6px 16px; background: var(--bg); border: 1px solid var(--border);
    color: var(--muted); cursor: pointer; transition: all 0.2s;
  }
  .spots-tab.active { background: var(--panel); color: var(--accent); border-bottom-color: var(--panel); }
  .spots-content { flex:1; position: relative; }
  .spots-iframe { width:100%; height:440px; border:none; display:none; }
  .spots-iframe.active { display:block; }

  /* scrollable table fallback */
  .spots-scroll { max-height: 400px; overflow-y: auto; }
  .spots-scroll::-webkit-scrollbar { width:4px; }
  .spots-scroll::-webkit-scrollbar-track { background:var(--bg); }
  .spots-scroll::-webkit-scrollbar-thumb { background:var(--border); }
  .spots-table { width:100%; border-collapse:collapse; font-family:'Share Tech Mono',monospace; font-size:11px; }
  .spots-table th { color:var(--muted); font-size:9px; letter-spacing:2px; text-align:left; padding:4px 8px; border-bottom:1px solid var(--border); font-family:'Inter',sans-serif; }
  .spots-table td { padding:5px 8px; border-bottom:1px solid rgba(26,45,69,0.5); white-space:nowrap; }
  .spots-table tr:hover td { background:rgba(0,212,255,0.04); }
  .spot-band { font-weight:bold; font-size:10px; padding:2px 5px; border-radius:2px; }
  .spot-dx   { color:var(--accent); }
  .spot-freq { color:var(--accent2); }
  .spot-de   { color:var(--muted); }
  .spot-comment { color:var(--text); font-size:10px; }
  .spot-time { color:var(--muted); }
  .spot-new { animation: fadeIn 1s ease; }
  @keyframes fadeIn { from{background:rgba(0,212,255,0.1)} to{background:transparent} }

  .loading { display:flex; align-items:center; justify-content:center; padding:20px; color:var(--muted); font-family:'Share Tech Mono',monospace; font-size:12px; letter-spacing:2px; }

  .panel::after {
    content:''; position:absolute; inset:0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events:none; opacity:0.4;
  }

  /* ── Storm Alert Banner ── */
  .storm-banner { display:none; position:sticky; top:0; z-index:200; }
  .storm-banner.visible { display:block; }
  .storm-inner { display:flex; align-items:center; gap:16px; padding:12px 24px; flex-wrap:wrap; }
  .storm-banner.CAUTION  .storm-inner { background:#3d2e00; border-bottom:3px solid #ffd700; }
  .storm-banner.WARNING  .storm-inner { background:#3d1400; border-bottom:3px solid #ff6b00; }
  .storm-banner.CRITICAL .storm-inner { background:#2d0000; border-bottom:3px solid #ff0000; animation:flash-red 0.8s infinite; }
  @keyframes flash-red { 0%,100%{background:#2d0000} 50%{background:#5a0000} }
  .storm-icon { font-size:26px; flex-shrink:0; }
  .storm-text { flex:1; }
  .storm-title { font-family:'Orbitron',monospace; font-size:13px; font-weight:700; letter-spacing:2px; margin-bottom:4px; }
  .storm-banner.CAUTION  .storm-title { color:#ffd700; }
  .storm-banner.WARNING  .storm-title { color:#ff8c00; }
  .storm-banner.CRITICAL .storm-title { color:#ff4444; text-shadow:0 0 10px rgba(255,68,68,0.8); }
  .storm-detail { font-family:'Share Tech Mono',monospace; font-size:11px; color:rgba(255,255,255,0.85); line-height:1.6; }
  .storm-dismiss { font-family:'Share Tech Mono',monospace; font-size:10px; letter-spacing:1px;
    padding:6px 14px; background:transparent; cursor:pointer; flex-shrink:0; transition:all 0.2s; border-radius:2px; }
  .storm-banner.CAUTION  .storm-dismiss { border:1px solid #ffd700; color:#ffd700; }
  .storm-banner.WARNING  .storm-dismiss { border:1px solid #ff8c00; color:#ff8c00; }
  .storm-banner.CRITICAL .storm-dismiss { border:1px solid #ff4444; color:#ff4444; }
  .storm-dismiss:hover { background:rgba(255,255,255,0.1); }
  .storm-status-pill { font-family:'Share Tech Mono',monospace; font-size:10px;
    padding:3px 10px; border-radius:2px; letter-spacing:1px; display:inline-block; margin-top:4px; }
  .storm-status-NONE     { color:var(--good); border:1px solid var(--good); background:rgba(57,255,20,0.08); }
  .storm-status-CAUTION  { color:#ffd700;     border:1px solid #ffd700;     background:rgba(255,215,0,0.12); }
  .storm-status-WARNING  { color:#ff8c00;     border:1px solid #ff8c00;     background:rgba(255,140,0,0.12); }
  .storm-status-CRITICAL { color:#ff4444;     border:1px solid #ff4444;     background:rgba(255,68,68,0.15); animation:flash-red 0.8s infinite; }
</style>
</head>
<body>

<!-- Storm Alert Banner -->
<div class="storm-banner" id="stormBanner">
  <div class="storm-inner">
    <div class="storm-icon" id="stormIcon">!</div>
    <div class="storm-text">
      <div class="storm-title" id="stormTitle">STORM ALERT</div>
      <div class="storm-detail" id="stormDetail">Checking weather data...</div>
    </div>
    <button class="storm-dismiss" onclick="dismissStorm()">X DISMISS</button>
  </div>
</div>

<header>
  <div>
    <div class="callsign">N4MI <span>EM83 &nbsp;·&nbsp; HF + 6M PROPAGATION DASHBOARD</span></div>
  </div>
  <div class="header-right">
    <div>
      <div class="utc-clock" id="utcClock">--:--:--</div>
      <div class="utc-label">UTC</div>
    </div>
    <button class="refresh-btn" onclick="refreshAll()">&#8635; REFRESH</button>
  </div>
</header>

<div class="solar-bar">
  <div class="solar-item">
    <div class="solar-label">SFI</div>
    <div class="solar-value" id="sfi" style="color:var(--accent)">--</div>
    <div class="solar-sub">Solar Flux</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">SSN</div>
    <div class="solar-value" id="ssn" style="color:var(--accent2)">--</div>
    <div class="solar-sub">Sunspot No.</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">A-INDEX</div>
    <div class="solar-value" id="aindex" style="color:var(--fair)">--</div>
    <div class="solar-sub">Geomagnetic</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">K-INDEX</div>
    <div class="solar-value" id="kindex" style="color:var(--fair)">--</div>
    <div class="solar-sub">Current</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">X-RAY</div>
    <div class="solar-value" id="xray" style="color:var(--text);font-size:16px">--</div>
    <div class="solar-sub">Solar Flares</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">SOLAR WIND</div>
    <div class="solar-value" id="solarwind" style="color:var(--text);font-size:16px">--</div>
    <div class="solar-sub">km/s</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">GEOMAG</div>
    <div class="solar-value" id="geomagfield" style="font-size:11px;margin-top:6px;color:var(--text)">--</div>
    <div class="solar-sub">Field Status</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">SIG NOISE</div>
    <div class="solar-value" id="signalnoise" style="color:var(--text);font-size:16px">--</div>
    <div class="solar-sub">S-Units</div>
  </div>
  <div class="solar-item">
    <div class="solar-label">CONDITIONS</div>
    <div class="solar-value" id="conditions" style="font-size:13px;margin-top:4px">--</div>
    <div class="solar-sub" id="condSub">Loading...</div>
  </div>
  <div class="solar-item">
  <div class="solar-item">
    <div class="solar-label">STORM STATUS</div>
    <div id="stormPill" class="storm-status-pill storm-status-NONE">ALL CLEAR</div>
    <div class="solar-sub" id="stormSub">Tempest + NWS</div>
  </div>
      <div class="solar-label">LAST UPDATE</div>
    <div class="solar-value" id="lastUpdate" style="font-size:11px;color:var(--muted);margin-top:4px">--</div>
    <div class="solar-sub">HamQSL / NOAA</div>
  </div>
</div>

<!-- HamQSL Widget Bar -->
<div style="background:var(--panel);border-bottom:1px solid var(--border);padding:10px 24px;display:flex;align-items:center;gap:20px;flex-wrap:wrap">
  <div style="font-family:'Orbitron',monospace;font-size:9px;letter-spacing:3px;color:var(--accent);white-space:nowrap">HAMQSL SOLAR DATA</div>
  <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center">
    <!-- HF Conditions Banner -->
    <a href="https://www.hamqsl.com/solar.html" title="HamQSL Solar Data" target="_blank">
      <img src="https://www.hamqsl.com/solar101vhf.php" style="height:170px;width:auto;border:none;display:block" alt="HamQSL Solar Widget - HF Conditions"/>
    </a>
    <!-- VHF/Aurora/Es Banner -->
    <a href="https://www.hamqsl.com/solar.html" title="HamQSL VHF Data" target="_blank">
      <img src="https://www.hamqsl.com/solarvhf.php" style="height:170px;width:auto;border:none;display:block" alt="HamQSL Solar Widget - VHF"/>
    </a>
    <!-- Solar Image Banner -->
    <a href="https://www.hamqsl.com/solar3.html" title="HamQSL Current Conditions" target="_blank">
      <img src="https://www.hamqsl.com/solar.php" style="height:170px;width:auto;border:none;display:block" alt="HamQSL Solar Widget - Solar Image"/>
    </a>
  </div>
  <div style="margin-left:auto;display:flex;flex-direction:column;gap:5px">
    <a href="https://www.hamqsl.com/solar3.html" target="_blank" class="cluster-link" style="font-size:9px;padding:5px 10px">&#9654; HAMQSL CONDITIONS</a>
    <a href="https://www.hamqsl.com/solar2.html" target="_blank" class="cluster-link" style="font-size:9px;padding:5px 10px">&#9654; HAMQSL DATA GUIDE</a>
    <a href="https://www.hamqsl.com/solar1.html" target="_blank" class="cluster-link" style="font-size:9px;padding:5px 10px">&#9654; HAMQSL TOOLS</a>
  </div>
</div>

<div class="main">

  <!-- Band Conditions -->
  <div class="panel band-panel">
    <div class="panel-title">BAND CONDITIONS · EM83</div>
    <div class="status-row" id="statusRow"><span class="loading">LOADING</span></div>
    <div class="band-grid" id="bandGrid"></div>
    <p class="data-note">Solar indices from NOAA SWPC. HamQSL widget updated every 3 hours. 80m/40m rated for D-layer absorption during day.</p>
  </div>

  <!-- MUF / Propagation Map (center) -->
  <div class="panel map-panel">
    <div class="panel-title">PROPAGATION MAP</div>
    <div style="display:flex;gap:6px;margin-bottom:8px;align-items:center">
      <div class="spots-tab active" style="padding:5px 14px;cursor:default">KC2G MUF</div>
      <a href="https://hf.dxview.org/perspective/EM83VK" target="_blank"
         style="font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:1px;padding:5px 14px;border:1px solid var(--accent2);color:var(--accent2);text-decoration:none;transition:all 0.2s"
         onmouseover="this.style.background='var(--accent2)';this.style.color='var(--bg)'"
         onmouseout="this.style.background='transparent';this.style.color='var(--accent2)'">
        &#9654; DXVIEW EM83 (NEW TAB)
      </a>
    </div>
    <div class="map-container">
      <iframe id="map-kc2g" style="width:100%;height:100%;border:none;min-height:340px;display:block" src="https://prop.kc2g.com/" title="KC2G MUF map" allowfullscreen loading="lazy"></iframe>
    </div>
  </div>

  <!-- Quick Links -->
  <div class="panel links-panel">
    <div class="panel-title">QUICK LINKS</div>

    <div class="link-section-label">PROPAGATION</div>
    <a class="cluster-link" href="https://prop.kc2g.com/" target="_blank">&#9654; PROP MAP (KC2G)</a>
    <a class="cluster-link" href="https://hf.dxview.org/perspective/EM83VK" target="_blank">&#9654; DXVIEW EM83VK</a>
    <a class="cluster-link" href="https://www.dxmaps.com/spots/map.php?Lan=E&Frec=0&ML=M&Map=NA&HF=1" target="_blank">&#9654; DXMAPS N.AMERICA</a>
    <a class="cluster-link" href="https://www.voacap.com/hf/index.html" target="_blank">&#9654; VOACAP PATH TOOL</a>
    <a class="cluster-link" href="https://www.hamqsl.com/solar.html" target="_blank">&#9654; HAMQSL SOLAR</a>
    <a class="cluster-link" href="https://www.hamqsl.com/solar3.html" target="_blank">&#9654; HAMQSL CONDITIONS</a>
    <a class="cluster-link" href="https://www.hamqsl.com/solar2.html" target="_blank">&#9654; HAMQSL DATA GUIDE</a>

    <div class="link-section-label">DX CLUSTER</div>
    <a class="cluster-link accent2" href="https://www.dxsummit.fi/#/" target="_blank">&#9654; DXSUMMIT</a>
    <a class="cluster-link accent2" href="https://holycluster.iarc.org/" target="_blank">&#9654; HOLY CLUSTER</a>
    <a class="cluster-link accent2" href="https://dxwatch.com/" target="_blank">&#9654; DXWATCH</a>

    <div class="link-section-label">LOGGING &amp; AWARDS</div>
    <a class="cluster-link" href="https://pskreporter.info/pskmap.html?preset&callsign=N4MI&mode=FT8&period=3600" target="_blank">&#9654; PSKREPORTER N4MI</a>
    <a class="cluster-link" href="https://www.qrz.com/lookup" target="_blank">&#9654; QRZ LOOKUP</a>
    <a class="cluster-link" href="https://lotw.arrl.org/lotwuser/default" target="_blank">&#9654; LOTW</a>
    <a class="cluster-link" href="https://clublog.org/loginform.php" target="_blank">&#9654; CLUBLOG</a>
    <a class="cluster-link" href="https://clublog.org/dxreport.html" target="_blank">&#9654; CLUBLOG DX REPORT</a>
    <a class="cluster-link" href="https://clublog.org/personal_spots.php" target="_blank">&#9654; CLUBLOG PERSONAL SPOTS</a>

    <div class="link-section-label">ALERTS</div>
    <a class="cluster-link accent2" href="https://hamalert.org/" target="_blank">&#9654; HAMALERT</a>

    <div class="link-section-label">DX EXPEDITIONS</div>
    <a class="cluster-link accent2" href="https://dxnews.com/calendar/" target="_blank">&#9654; DXNEWS CALENDAR</a>
  </div>

  <!-- DX Cluster Spots -->
  <div class="panel spots-panel">
    <div class="panel-title">DX CLUSTER SPOTS &nbsp;·&nbsp; HOLY CLUSTER LIVE</div>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
      <a href="https://www.dxsummit.fi/#/" target="_blank" style="font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:1px;padding:7px 18px;border:1px solid var(--accent2);color:var(--accent2);text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='var(--accent2)';this.style.color='var(--bg)'" onmouseout="this.style.background='transparent';this.style.color='var(--accent2)'">&#9654; OPEN DXSUMMIT IN NEW TAB</a>
      <a href="https://dxwatch.com/" target="_blank" style="font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:1px;padding:7px 18px;border:1px solid var(--accent2);color:var(--accent2);text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='var(--accent2)';this.style.color='var(--bg)'" onmouseout="this.style.background='transparent';this.style.color='var(--accent2)'">&#9654; OPEN DXWATCH IN NEW TAB</a>
      <a href="https://holycluster.iarc.org/" target="_blank" style="font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:1px;padding:7px 18px;border:1px solid var(--muted);color:var(--muted);text-decoration:none" >&#9654; OPEN HOLY CLUSTER IN NEW TAB</a>
    </div>
    <div class="spots-content">
      <iframe class="spots-iframe active" src="https://holycluster.iarc.org/" loading="lazy"></iframe>
    </div>
    <p class="data-note">Holy Cluster embedded live above. DXSummit and DXWatch block embedding — use the buttons above to open them in a new tab.</p>
  </div>

</div>

<script>
// UTC Clock
function updateClock() {
  const n = new Date();
  document.getElementById('utcClock').textContent =
    String(n.getUTCHours()).padStart(2,'0') + ':' +
    String(n.getUTCMinutes()).padStart(2,'0') + ':' +
    String(n.getUTCSeconds()).padStart(2,'0');
}
setInterval(updateClock,1000); updateClock();

// Tab switching
function showTab(name, el) {
  document.querySelectorAll('.spots-iframe').forEach(f => f.classList.remove('active'));
  document.querySelectorAll('.spots-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('iframe-' + name).classList.add('active');
  el.classList.add('active');
}

// Band config
const bandColors = {
  '80m':'var(--band80)','40m':'var(--band40)','20m':'var(--band20)','17m':'var(--band17)',
  '15m':'var(--band15)','12m':'var(--band12)','10m':'var(--band10)','6m':'var(--band6)'
};
const bandClass = {'80m':'b80','40m':'b40','20m':'b20','17m':'b17','15m':'b15','12m':'b12','10m':'b10','6m':'b6'};
const bandFreqs = {
  '80m':[3500,4000],'40m':[7000,7300],'20m':[14000,14350],'17m':[18068,18168],
  '15m':[21000,21450],'12m':[24890,24990],'10m':[28000,29700],'6m':[50000,54000]
};

// Solar data - HamQSL proxy (primary) + NOAA fallback
async function fetchSolarData() {
  let sfi=0, ssn=0, kIdx=0, aIdx='--';

  // Try HamQSL proxy first (richest data)
  try {
    const hqRes = await fetch('/api/hamqsl');
    if (hqRes.ok) {
      const hq = await hqRes.json();
      if (!hq.error) {
        sfi   = parseFloat(hq.solarflux) || 0;
        ssn   = parseFloat(hq.sunspots)  || 0;
        kIdx  = parseFloat(hq.kindex)    || 0;
        aIdx  = parseFloat(hq.aindex) >= 0 ? Math.round(parseFloat(hq.aindex)) : '--';

        // Extra fields
        const xray = hq.xray || '--';
        const sw   = hq.solarwind ? Math.round(parseFloat(hq.solarwind)) + '' : '--';
        const geo  = hq.geomagfield || '--';
        const sn   = hq.signalnoise || '--';

        document.getElementById('xray').textContent      = xray;
        document.getElementById('solarwind').textContent = sw !== 'NaN' ? sw : '--';
        document.getElementById('geomagfield').textContent = geo;
        document.getElementById('signalnoise').textContent = sn;

        // Color X-ray
        const xEl = document.getElementById('xray');
        if      (xray.startsWith('X')) xEl.style.color = 'var(--poor)';
        else if (xray.startsWith('M')) xEl.style.color = 'var(--fair)';
        else if (xray.startsWith('C')) xEl.style.color = 'var(--accent2)';
        else                           xEl.style.color = 'var(--good)';

        // Color solar wind
        const swVal = parseFloat(sw);
        const swEl = document.getElementById('solarwind');
        if      (swVal >= 500) swEl.style.color = 'var(--poor)';
        else if (swVal >= 400) swEl.style.color = 'var(--fair)';
        else                   swEl.style.color = 'var(--good)';

        // Update timestamp from HamQSL
        if (hq.updated) {
          document.getElementById('lastUpdate').textContent = hq.updated;
        }
        console.log('Solar data from HamQSL proxy');
      }
    }
  } catch(e) {
    console.warn('HamQSL proxy failed, trying NOAA...', e);
  }

  // NOAA fallback or supplement
  if (!sfi) {
    try {
      const [cycleRes, kRes, aRes] = await Promise.all([
        fetch('https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json'),
        fetch('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),
        fetch('https://services.swpc.noaa.gov/products/noaa-planetary-a-index.json'),
      ]);
      const cycleData = await cycleRes.json();
      const kData     = await kRes.json();
      const aData     = await aRes.json();

      const latest = cycleData[cycleData.length-1];
      sfi = Math.round(parseFloat(latest['f10.7']) || 0);
      ssn = Math.round(parseFloat(latest['ssn'])   || 0);

      const kRows   = kData.slice(1);
      const kLatest = kRows[kRows.length-1];
      kIdx = parseFloat(kLatest[1]) || 0;

      try {
        const aRows = Array.isArray(aData) ? aData.slice(1) : [];
        if (aRows.length) {
          const aLast = aRows[aRows.length-1];
          const aVal  = parseFloat(Array.isArray(aLast) ? aLast[1] : aLast.a);
          if (!isNaN(aVal) && aVal >= 0) aIdx = Math.round(aVal);
        }
      } catch(e) {}

      const now = new Date();
      document.getElementById('lastUpdate').textContent =
        String(now.getUTCHours()).padStart(2,'0') + ':' + String(now.getUTCMinutes()).padStart(2,'0') + ' UTC';

      console.log('Solar data from NOAA fallback');
    } catch(e) {
      console.error('Both solar sources failed:', e);
      document.getElementById('conditions').textContent = 'ERROR';
      document.getElementById('condSub').textContent = 'Check network';
      return;
    }
  }

  // Update solar bar
  document.getElementById('sfi').textContent = sfi || '--';
  document.getElementById('ssn').textContent = ssn || '--';
  document.getElementById('aindex').textContent = aIdx;
  document.getElementById('kindex').textContent = kIdx.toFixed ? kIdx.toFixed(1) : kIdx;

  const aEl = document.getElementById('aindex');
  const aVal = parseFloat(aIdx);
  if (!isNaN(aVal)) aEl.style.color = aVal<=7 ? 'var(--good)' : aVal<=29 ? 'var(--fair)' : 'var(--poor)';

  const kEl = document.getElementById('kindex');
  kEl.style.color = kIdx<=2 ? 'var(--good)' : kIdx<=4 ? 'var(--fair)' : 'var(--poor)';

  let cond, condColor, condSub;
  if      (kIdx>=5)               { cond='DISTURBED'; condColor='var(--poor)'; condSub='Geomagnetic storm'; }
  else if (kIdx<=2 && sfi>=150)   { cond='EXCELLENT'; condColor='var(--good)'; condSub='High flux, quiet geo'; }
  else if (kIdx<=2 && sfi>=110)   { cond='GOOD';      condColor='var(--good)'; condSub='Favorable conditions'; }
  else if (kIdx<=3 && sfi>=90)    { cond='FAIR';      condColor='var(--fair)'; condSub='Moderate conditions'; }
  else                            { cond='POOR';       condColor='var(--poor)'; condSub='Low solar activity'; }

  document.getElementById('conditions').textContent = cond;
  document.getElementById('conditions').style.color = condColor;
  document.getElementById('condSub').textContent    = condSub;

  updateBandConditions(sfi, kIdx);
}

// ── Band condition model ──────────────────────────────────
// Properly accounts for D-layer absorption on 80m/40m during daylight.
// EM83 local noon ~ 17:00-18:00 UTC. Dawn ~11 UTC, dusk ~23 UTC.
function getTimeOfDay(utcHour) {
  // Returns: 'night', 'dawn', 'day', 'dusk'
  if (utcHour >= 12 && utcHour < 22) return 'day';
  if (utcHour >= 22 || utcHour < 1)  return 'dusk';
  if (utcHour >= 1  && utcHour < 11) return 'night';
  return 'dawn'; // 11-12 UTC
}

function rateBand(sfi, kIdx, band, tod) {
  // Geomagnetic penalty
  const geo = kIdx<=2 ? 1.0 : kIdx<=4 ? 0.65 : 0.25;

  // Band models:
  // Low bands (80/40): excellent at night, poor during day due to D-layer absorption
  // Mid bands (20/17/15): best during day, depend heavily on SFI
  // High bands (12/10/6): only open with high SFI, mostly day

  const models = {
    //          night  dawn   day    dusk   (SFI thresholds for fair/good)
    '80m': { night:[70,90],  dawn:[80,110], day:[999,999], dusk:[80,110] },
    '40m': { night:[70,90],  dawn:[75,95],  day:[130,160], dusk:[75,95]  },
    '20m': { night:[95,125], dawn:[85,110], day:[80,105],  dusk:[85,110] },
    '17m': { night:[105,135],dawn:[95,120], day:[90,115],  dusk:[95,120] },
    '15m': { night:[120,150],dawn:[110,140],day:[105,135], dusk:[110,140]},
    '12m': { night:[140,170],dawn:[130,160],day:[120,150], dusk:[130,160]},
    '10m': { night:[155,185],dawn:[145,175],day:[130,165], dusk:[145,175]},
    '6m':  { night:[999,999],dawn:[160,190],day:[150,185], dusk:[160,190]},
  };

  const [fairThresh, goodThresh] = models[band][tod];
  const score = sfi * geo;

  if (score >= goodThresh) return 'good';
  if (score >= fairThresh) return 'fair';
  return 'poor';
}

function updateBandConditions(sfi, kIdx) {
  const utcHour = new Date().getUTCHours();
  const tod = getTimeOfDay(utcHour);
  const todLabel = { night:'NIGHT', dawn:'DAWN', day:'DAY', dusk:'DUSK' }[tod];

  const bandIds = ['80m','40m','20m','17m','15m','12m','10m','6m'];
  const bands = bandIds.map(id => ({
    id,
    rating: rateBand(sfi, kIdx, id, tod),
    // Also compute adjacent period for reference
    altTod: tod === 'day' ? 'night' : 'day',
    altRating: rateBand(sfi, kIdx, id, tod === 'day' ? 'night' : 'day'),
  }));

  const statusRow = document.getElementById('statusRow');
  statusRow.innerHTML = `<span style="font-family:'Share Tech Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:1px;margin-right:6px">${todLabel}</span>`;
  ['good','fair','poor'].forEach(r => {
    const bs = bands.filter(b=>b.rating===r).map(b=>b.id);
    if (bs.length) statusRow.innerHTML += `<span class="status-pill ${r}">${r.toUpperCase()}: ${bs.join(' ')}</span>`;
  });

  const grid = document.getElementById('bandGrid');
  grid.innerHTML = '';
  bands.forEach(b => {
    const card = document.createElement('div');
    card.className = 'band-card ' + bandClass[b.id];
    const altLabel = tod==='day' ? 'Night' : 'Day';
    card.innerHTML = `
      <span class="band-name">${b.id.toUpperCase()}</span>
      <div class="band-status ${b.rating}">${b.rating.toUpperCase()}</div>
      <div class="band-detail">${altLabel}: ${b.altRating} &nbsp;|&nbsp; ${bandFreqs[b.id][0]}-${bandFreqs[b.id][1]} kHz</div>
    `;
    grid.appendChild(card);
  });
}


// ── Storm Alert System ──────────────────────────────────
var stormDismissed = false;
var lastStormLevel = 'NONE';

function fetchStormStatus() {
  fetch('/api/storm')
    .then(function(res) {
      if (!res.ok) throw new Error('Storm API not available');
      return res.json();
    })
    .then(function(data) {
      var level  = data.level || 'NONE';
      var banner = document.getElementById('stormBanner');
      var pill   = document.getElementById('stormPill');
      var sub    = document.getElementById('stormSub');
      var icon   = document.getElementById('stormIcon');
      var title  = document.getElementById('stormTitle');
      var detail = document.getElementById('stormDetail');

      // Update solar bar pill
      pill.className   = 'storm-status-pill storm-status-' + level;
      pill.textContent = (level === 'NONE') ? 'ALL CLEAR' : level;
      if (data.last_updated) { sub.textContent = 'Updated ' + data.last_updated; }

      // Build detail lines
      var lines = [];
      if (data.lightning_km !== null && data.lightning_km !== undefined
          && data.lightning_ago !== null && data.lightning_ago !== undefined) {
        var dist  = (data.lightning_km < 1) ? '<1' : Math.round(data.lightning_km);
        var miles = Math.round(data.lightning_km * 0.621);
        lines.push('Lightning: ' + dist + ' km (' + miles + ' mi) | '
          + Math.round(data.lightning_ago) + ' min ago | '
          + (data.lightning_1hr || 0) + ' strikes/hr');
      }
      if (data.wind_gust) { lines.push('Wind gust: ' + data.wind_gust + ' mph'); }
      if (data.nws_alerts && data.nws_alerts.length > 0) {
        data.nws_alerts.forEach(function(a) {
          lines.push('NWS: ' + a.event + (a.headline ? ' - ' + a.headline : ''));
        });
      }
      if (data.conditions) { lines.push('Conditions: ' + data.conditions); }

      // Un-dismiss if level escalates
      if (level !== 'NONE' && level !== lastStormLevel) { stormDismissed = false; }
      lastStormLevel = level;

      // Show or hide banner
      if (level !== 'NONE' && !stormDismissed) {
        var icons  = { CAUTION:'(!)', WARNING:'(!!)', CRITICAL:'[!!!]' };
        var titles = {
          CAUTION:  'WEATHER CAUTION -- MONITOR CONDITIONS',
          WARNING:  'STORM WARNING -- CONSIDER LOWERING TOWER',
          CRITICAL: 'SEVERE STORM WARNING -- LOWER TOWER NOW!'
        };
        banner.className  = 'storm-banner visible ' + level;
        icon.textContent  = icons[level]  || '(!)';
        title.textContent = titles[level] || 'STORM ALERT';
        detail.innerHTML  = lines.join('<br>');
      } else if (level === 'NONE') {
        banner.className = 'storm-banner';
      }
    })
    .catch(function(e) {
      console.log('Storm API:', e.message);
    });
}

function dismissStorm() {
  stormDismissed = true;
  document.getElementById('stormBanner').className = 'storm-banner';
}

setInterval(fetchStormStatus, 60000);
fetchStormStatus();

function refreshAll() {
  fetchSolarData();
}

setInterval(refreshAll, 5*60*1000);
refreshAll();
</script>
</body>
</html>
