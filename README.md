# 📡 4G LTE Network Performance Monitoring, Fault Detection & Root-Cause Analysis (RCA) System

A production-grade 4G LTE Network Operations Center (NOC) performance monitoring, fault detection, and automated Root Cause Analysis (RCA) system built to simulate 3GPP telemetry, continuous KPI threshold analysis, multi-tier alarm generation, and real-time network optimization.

---

## 🚀 Key Features & Capabilities

- **📡 Live 3GPP Telemetry Engine**: Monitors 50 Cell Sectors across 10 eNodeBs on Band 3 (1800MHz), Band 5 (850MHz), and Band 40 (2300MHz).
- **📊 13 Real-time 3GPP KPIs**: Tracks Availability %, RSRP (dBm), RSRQ (dB), SINR (dB), Throughput DL/UL (Mbps), Latency (ms), PRB Utilization %, Call Drop Rate %, Handover Success Rate %, Attach Success Rate %, Packet Loss %, and Active Users.
- **🧠 Automated Root Cause Analysis (RCA)**: Rule-based heuristics classifying anomalies into:
  - 🚨 **RAN Traffic Congestion**
  - 💥 **eNodeB / Site Outage**
  - 📡 **Pilot Pollution / Interference**
  - 📉 **Cell Edge Coverage Hole**
  - 🌐 **S1 Backhaul Transport Fade**
  - 🔄 **Mobility / Handover Failure**
- **🎛️ Dark Mode Telecom NOC Dashboard**:
  - Executive NOC Wallboard & 50-Cell Topology Heatmap Grid.
  - Interactive Fault Injection Simulator.
  - Alarms Stream & One-Click Automated Remediation Modal.
  - SQLite Query Studio & SLA Threshold Configurator.
  - 4G/3G/2G Telecom Fundamentals & Jio Technical Interview Prep Guide.

---

## 🛠️ Tech Stack

- **Backend / Telemetry Engine**: Python 3, SQLite, Multi-threading, Standard HTTP REST API.
- **Frontend Dashboard**: HTML5, Vanilla CSS, JavaScript (ES6+), Google Fonts (Outfit, Inter, JetBrains Mono), Lucide Icons, Chart.js, KaTeX.

---

## 📁 Repository Structure

```
lte-network-monitor/
├── lte_engine.py         # 3GPP Telemetry Generator, RCA Logic & SQLite Manager
├── server.py             # Full-stack Python HTTP REST API & Web Dashboard Server
├── lte_network.db        # SQLite Database storing telemetry logs & active alarms
├── public/
│   └── index.html        # NOC Control Center Web Application
├── README.md             # Documentation & Setup Guide
└── .gitignore
```

---

## ⚡ Quick Start Guide

### 1. Run Web Dashboard Server
```bash
python server.py
```
Open your browser to: **`http://localhost:8000`**

### 2. Run CLI Engine & Fault Simulator
```bash
# Run self-test suite
python lte_engine.py --test

# Inject congestion fault into CELL_102_B
python lte_engine.py --generate 5 --fault CONGESTION --cell CELL_102_B

# Execute raw SQL query against lte_network.db
python lte_engine.py --sql "SELECT cell_id, prb_utilization, throughput_dl FROM telemetry_logs WHERE prb_utilization > 85"
```

---

## 📜 License
MIT License - Open Source for Telecom Network Engineers & Researchers.
