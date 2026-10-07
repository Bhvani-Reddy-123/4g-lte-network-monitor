#!/usr/bin/env python3
"""
4G LTE Network Performance Monitoring, Fault Detection & Root-Cause Analysis (RCA) Engine
Author: Antigravity AI Team
Description: Telecom NOC engine providing 3GPP LTE telemetry generation, threshold monitoring,
             multi-tier alarm classification, automated Root Cause Analysis, and SQLite logging.
"""

import sys
import os
import json
import sqlite3
import random
import time
import argparse
from datetime import datetime, timedelta

# Fix Windows console UTF-8 output encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lte_network.db")

# 3GPP Benchmark Thresholds
THRESHOLDS = {
    "availability_min": 98.0,          # %
    "rsrp_min": -110.0,                # dBm (Below is poor coverage)
    "rsrq_min": -13.0,                 # dB (Below is poor quality)
    "sinr_min": 5.0,                   # dB (Below is high noise/interference)
    "throughput_dl_min": 10.0,         # Mbps
    "latency_max": 60.0,               # ms
    "prb_utilization_max": 85.0,       # % (Above is congestion)
    "call_drop_rate_max": 1.5,         # %
    "handover_success_min": 95.0,      # %
    "attach_success_min": 96.0,        # %
    "packet_loss_max": 1.5             # %
}

# Cell & eNodeB Topology Setup
ENODEBS = [f"eNodeB_{101 + i}" for i in range(10)]
SECTORS = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
CELLS = []
for enb in ENODEBS:
    for s_idx, sec in enumerate(SECTORS):
        cell_id = f"CELL_{enb.split('_')[1]}_{chr(65+s_idx)}"
        CELLS.append({
            "cell_id": cell_id,
            "enodeb_id": enb,
            "sector": sec,
            "band": random.choice(["Band 3 (1800MHz)", "Band 5 (850MHz)", "Band 40 (2300MHz)"]),
            "pci": random.randint(1, 503)
        })

def init_db():
    """Initialize SQLite database for LTE telemetry and alarms log."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cell_id TEXT NOT NULL,
        enodeb_id TEXT NOT NULL,
        availability REAL,
        rsrp REAL,
        rsrq REAL,
        sinr REAL,
        throughput_dl REAL,
        throughput_ul REAL,
        latency REAL,
        prb_utilization REAL,
        call_drop_rate REAL,
        handover_success_rate REAL,
        attach_success_rate REAL,
        packet_loss REAL,
        active_users INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cell_id TEXT NOT NULL,
        enodeb_id TEXT NOT NULL,
        severity TEXT NOT NULL,
        category TEXT NOT NULL,
        probable_cause TEXT NOT NULL,
        evidence TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    conn.commit()
    conn.close()

def generate_cell_telemetry(cell_info, fault_override=None):
    """Generates synthetic LTE telemetry data for a cell, with optional fault injection."""
    now_str = datetime.now().isoformat()
    
    # Baseline normal telemetry
    telemetry = {
        "timestamp": now_str,
        "cell_id": cell_info["cell_id"],
        "enodeb_id": cell_info["enodeb_id"],
        "availability": round(random.uniform(99.5, 100.0), 2),
        "rsrp": round(random.uniform(-98.0, -75.0), 1),
        "rsrq": round(random.uniform(-11.0, -6.0), 1),
        "sinr": round(random.uniform(12.0, 25.0), 1),
        "throughput_dl": round(random.uniform(25.0, 95.0), 2),
        "throughput_ul": round(random.uniform(10.0, 35.0), 2),
        "latency": round(random.uniform(20.0, 45.0), 1),
        "prb_utilization": round(random.uniform(35.0, 75.0), 1),
        "call_drop_rate": round(random.uniform(0.1, 0.8), 2),
        "handover_success_rate": round(random.uniform(97.5, 99.9), 2),
        "attach_success_rate": round(random.uniform(98.0, 100.0), 2),
        "packet_loss": round(random.uniform(0.1, 0.9), 2),
        "active_users": random.randint(40, 220)
    }

    if fault_override:
        fault_type = fault_override.upper()
        if fault_type == "CONGESTION":
            telemetry["prb_utilization"] = round(random.uniform(94.0, 99.5), 1)
            telemetry["throughput_dl"] = round(random.uniform(1.2, 4.5), 2)
            telemetry["latency"] = round(random.uniform(85.0, 160.0), 1)
            telemetry["active_users"] = random.randint(380, 490)
        elif fault_type == "SITE_OUTAGE":
            telemetry["availability"] = round(random.uniform(45.0, 72.0), 1)
            telemetry["attach_success_rate"] = round(random.uniform(20.0, 55.0), 2)
            telemetry["throughput_dl"] = 0.0
            telemetry["throughput_ul"] = 0.0
            telemetry["packet_loss"] = round(random.uniform(18.0, 45.0), 2)
        elif fault_type == "INTERFERENCE":
            telemetry["rsrp"] = round(random.uniform(-88.0, -78.0), 1)  # Good RSRP
            telemetry["sinr"] = round(random.uniform(-4.0, 2.5), 1)     # High interference!
            telemetry["call_drop_rate"] = round(random.uniform(3.2, 7.8), 2)
            telemetry["rsrq"] = round(random.uniform(-17.0, -14.0), 1)
        elif fault_type == "COVERAGE_HOLE":
            telemetry["rsrp"] = round(random.uniform(-128.0, -116.0), 1)
            telemetry["rsrq"] = round(random.uniform(-18.0, -14.5), 1)
            telemetry["handover_success_rate"] = round(random.uniform(65.0, 82.0), 2)
            telemetry["call_drop_rate"] = round(random.uniform(4.0, 9.5), 2)
        elif fault_type == "TRANSPORT_BACKHAUL":
            telemetry["packet_loss"] = round(random.uniform(4.5, 12.0), 2)
            telemetry["latency"] = round(random.uniform(130.0, 280.0), 1)
            telemetry["prb_utilization"] = round(random.uniform(30.0, 55.0), 1) # PRB normal but backhaul choke
            telemetry["throughput_dl"] = round(random.uniform(3.0, 8.0), 2)
        elif fault_type == "MOBILITY_FAILURE":
            telemetry["handover_success_rate"] = round(random.uniform(68.0, 84.0), 2)
            telemetry["call_drop_rate"] = round(random.uniform(3.5, 6.8), 2)
            telemetry["rsrp"] = round(random.uniform(-92.0, -84.0), 1)

    return telemetry

def perform_root_cause_analysis(telemetry):
    """
    RCA Engine evaluating telemetry metrics against rules to classify alarm and probable cause.
    Returns alarm dict or None if metrics are normal.
    """
    cell_id = telemetry["cell_id"]
    enodeb_id = telemetry["enodeb_id"]
    timestamp = telemetry["timestamp"]

    # 1. Check Site Outage
    if telemetry["availability"] < THRESHOLDS["availability_min"] or telemetry["attach_success_rate"] < 70.0:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "CRITICAL",
            "category": "SITE_OUTAGE",
            "probable_cause": "eNodeB hardware fault or IP transport link disconnection",
            "evidence": f"Availability: {telemetry['availability']}% (min {THRESHOLDS['availability_min']}%), Attach Success: {telemetry['attach_success_rate']}%",
            "recommended_action": "Check site physical connectivity, optical transceiver SFP status, power supply & backhaul link.",
            "status": "ACTIVE"
        }

    # 2. Check Network Congestion
    if telemetry["prb_utilization"] >= THRESHOLDS["prb_utilization_max"] and telemetry["latency"] > 70.0 and telemetry["throughput_dl"] < 6.0:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "HIGH",
            "category": "CONGESTION",
            "probable_cause": "Radio Access Network (RAN) Spectral Congestion",
            "evidence": f"PRB Util: {telemetry['prb_utilization']}% (max {THRESHOLDS['prb_utilization_max']}%), DL Throughput: {telemetry['throughput_dl']} Mbps, Latency: {telemetry['latency']} ms",
            "recommended_action": "Enable Carrier Aggregation (CA), steer traffic to underutilized 1800MHz/2300MHz bands, or upgrade site PRB capacity.",
            "status": "ACTIVE"
        }

    # 3. Check Pilot Pollution / Interference
    if telemetry["rsrp"] > -95.0 and telemetry["sinr"] < THRESHOLDS["sinr_min"] and telemetry["call_drop_rate"] > 2.0:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "HIGH",
            "category": "INTERFERENCE",
            "probable_cause": "Pilot Pollution / Co-Channel Interference (PCI Collision)",
            "evidence": f"RSRP: {telemetry['rsrp']} dBm (strong), but SINR: {telemetry['sinr']} dB (min {THRESHOLDS['sinr_min']} dB), Drop Rate: {telemetry['call_drop_rate']}%",
            "recommended_action": "Adjust antenna Remote Electrical Tilt (RET), re-plan Physical Cell Identity (PCI), tune neighbor cell azimuth.",
            "status": "ACTIVE"
        }

    # 4. Check Weak Coverage / Cell Edge
    if telemetry["rsrp"] < THRESHOLDS["rsrp_min"] or telemetry["rsrq"] < THRESHOLDS["rsrq_min"]:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "MEDIUM",
            "category": "COVERAGE_HOLE",
            "probable_cause": "Weak RF propagation / Building obstruction / Cell edge attenuation",
            "evidence": f"RSRP: {telemetry['rsrp']} dBm (min {THRESHOLDS['rsrp_min']} dBm), RSRQ: {telemetry['rsrq']} dB (min {THRESHOLDS['rsrq_min']} dB)",
            "recommended_action": "Increase eNodeB maximum Tx power, lower antenna tilt angle, evaluate small cell extension deployment.",
            "status": "ACTIVE"
        }

    # 5. Check IP Transport / Backhaul Link
    if telemetry["packet_loss"] > THRESHOLDS["packet_loss_max"] and telemetry["latency"] > 100.0 and telemetry["prb_utilization"] < 60.0:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "HIGH",
            "category": "TRANSPORT_BACKHAUL",
            "probable_cause": "S1-U Backhaul Transport Congestion or Microwave Link Fading",
            "evidence": f"Packet Loss: {telemetry['packet_loss']}% (max {THRESHOLDS['packet_loss_max']}%), Latency: {telemetry['latency']} ms with normal PRB ({telemetry['prb_utilization']}%)",
            "recommended_action": "Audit S1 transport router VLAN QoS priority queues, verify microwave ACM link modulation level.",
            "status": "ACTIVE"
        }

    # 6. Check Mobility / Handover Failure
    if telemetry["handover_success_rate"] < THRESHOLDS["handover_success_min"] and telemetry["call_drop_rate"] > 1.5:
        return {
            "timestamp": timestamp,
            "cell_id": cell_id,
            "enodeb_id": enodeb_id,
            "severity": "MEDIUM",
            "category": "MOBILITY_FAILURE",
            "probable_cause": "Handover Parameter Misconfiguration (A3-Offset / Time-To-Trigger)",
            "evidence": f"Handover Success: {telemetry['handover_success_rate']}% (min {THRESHOLDS['handover_success_min']}%), Call Drop: {telemetry['call_drop_rate']}%",
            "recommended_action": "Adjust A3 event offset hysteresis, check X2 interface connectivity with adjacent eNodeBs.",
            "status": "ACTIVE"
        }

    return None

def save_to_db(telemetry, alarm=None):
    """Saves telemetry log and optional alarm event to SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO telemetry_logs (
        timestamp, cell_id, enodeb_id, availability, rsrp, rsrq, sinr,
        throughput_dl, throughput_ul, latency, prb_utilization, call_drop_rate,
        handover_success_rate, attach_success_rate, packet_loss, active_users
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        telemetry["timestamp"], telemetry["cell_id"], telemetry["enodeb_id"],
        telemetry["availability"], telemetry["rsrp"], telemetry["rsrq"], telemetry["sinr"],
        telemetry["throughput_dl"], telemetry["throughput_ul"], telemetry["latency"],
        telemetry["prb_utilization"], telemetry["call_drop_rate"], telemetry["handover_success_rate"],
        telemetry["attach_success_rate"], telemetry["packet_loss"], telemetry["active_users"]
    ))

    if alarm:
        cursor.execute("""
        INSERT INTO alarms (
            timestamp, cell_id, enodeb_id, severity, category,
            probable_cause, evidence, recommended_action, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alarm["timestamp"], alarm["cell_id"], alarm["enodeb_id"],
            alarm["severity"], alarm["category"], alarm["probable_cause"],
            alarm["evidence"], alarm["recommended_action"], alarm["status"]
        ))

    conn.commit()
    conn.close()

def run_simulation(count=5, fault_cell=None, fault_type=None):
    """Runs N simulation cycles generating telemetry, detecting alarms, and logging."""
    init_db()
    print(f"\n========================================================")
    print(f"📡 4G LTE TELEMETRY ENGINE & RCA ANALYZER INITIATED")
    print(f"========================================================")
    print(f"Monitoring {len(CELLS)} cells across {len(ENODEBS)} eNodeBs...")
    if fault_cell and fault_type:
        print(f"⚠️ FAULT INJECTION ACTIVE: Cell '{fault_cell}' -> Fault '{fault_type}'")

    alarm_count = 0
    for cycle in range(1, count + 1):
        print(f"\n--- Simulation Cycle {cycle}/{count} [{datetime.now().strftime('%H:%M:%S')}] ---")
        cycle_alarms = 0
        
        # Pick 5 random cells each cycle to sample
        sample_cells = random.sample(CELLS, min(8, len(CELLS)))
        
        # If fault injection specified, make sure target cell is in sample
        if fault_cell:
            target = next((c for c in CELLS if c["cell_id"] == fault_cell), None)
            if target and target not in sample_cells:
                sample_cells[0] = target

        for cell in sample_cells:
            f_override = fault_type if (fault_cell and cell["cell_id"] == fault_cell) else None
            telem = generate_cell_telemetry(cell, fault_override=f_override)
            alarm = perform_root_cause_analysis(telem)
            save_to_db(telem, alarm)

            if alarm:
                cycle_alarms += 1
                alarm_count += 1
                icon = "🚨" if alarm["severity"] in ["CRITICAL", "HIGH"] else "⚠️"
                print(f"{icon} [{alarm['severity']}] {alarm['cell_id']} ({alarm['category']}): {alarm['probable_cause']}")
                print(f"   ├─ Evidence: {alarm['evidence']}")
                print(f"   └─ Action:   {alarm['recommended_action']}")

        if cycle_alarms == 0:
            print("✅ All sampled cells operating within normal 3GPP threshold parameters.")
        
        time.sleep(0.5)

    print(f"\n========================================================")
    print(f"✅ Simulation Complete. Total Alarms Logged: {alarm_count}")
    print(f"📁 SQLite Database File: {DB_FILE}")
    print(f"========================================================\n")

def execute_sql(query):
    """Executes custom SQL query on lte_network.db and outputs formatted text table."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description] if cursor.description else []
        print(f"\n📊 SQL Query: {query}")
        print("-" * 60)
        print(" | ".join(headers))
        print("-" * 60)
        for r in rows:
            print(" | ".join(str(val) for val in r))
        print("-" * 60)
        print(f"Total Rows Returned: {len(rows)}\n")
    except Exception as e:
        print(f"❌ SQL Execution Error: {e}")
    finally:
        conn.close()

def run_tests():
    """Runs automated unit test verification of telemetry generation, RCA rules, and DB persistence."""
    print("\n🧪 RUNNING LTE ENGINE SELF-TEST SYSTEM...")
    init_db()
    
    # 1. Test Baseline Telemetry
    sample_cell = CELLS[0]
    telem = generate_cell_telemetry(sample_cell)
    assert telem["cell_id"] == sample_cell["cell_id"], "Cell ID mismatch"
    assert "rsrp" in telem and "prb_utilization" in telem, "Missing telemetry key"
    print("  [PASS] 1. Baseline Telemetry Generation")

    # 2. Test Congestion RCA
    cong_telem = generate_cell_telemetry(sample_cell, fault_override="CONGESTION")
    alarm_cong = perform_root_cause_analysis(cong_telem)
    assert alarm_cong is not None and alarm_cong["category"] == "CONGESTION", "Congestion RCA failed"
    print("  [PASS] 2. Congestion Fault RCA Rule")

    # 3. Test Interference RCA
    interf_telem = generate_cell_telemetry(sample_cell, fault_override="INTERFERENCE")
    alarm_interf = perform_root_cause_analysis(interf_telem)
    assert alarm_interf is not None and alarm_interf["category"] == "INTERFERENCE", "Interference RCA failed"
    print("  [PASS] 3. Interference / Pilot Pollution RCA Rule")

    # 4. Test Site Outage RCA
    outage_telem = generate_cell_telemetry(sample_cell, fault_override="SITE_OUTAGE")
    alarm_outage = perform_root_cause_analysis(outage_telem)
    assert alarm_outage is not None and alarm_outage["severity"] == "CRITICAL", "Site Outage RCA failed"
    print("  [PASS] 4. Site Outage Critical Alarm Rule")

    # 5. Test DB Insertion
    save_to_db(telem, alarm_cong)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM telemetry_logs")
    count_t = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM alarms")
    count_a = c.fetchone()[0]
    conn.close()
    assert count_t > 0 and count_a > 0, "DB Insertion failed"
    print("  [PASS] 5. SQLite Database Persistence")

    print("🎉 ALL LTE ENGINE SELF-TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="4G LTE Network Performance Engine & RCA System")
    parser.add_argument("--generate", type=int, help="Run N simulation cycles")
    parser.add_argument("--fault", type=str, help="Fault type (CONGESTION, SITE_OUTAGE, INTERFERENCE, COVERAGE_HOLE, TRANSPORT_BACKHAUL, MOBILITY_FAILURE)")
    parser.add_argument("--cell", type=str, help="Target cell ID for fault injection (e.g. CELL_101_A)")
    parser.add_argument("--sql", type=str, help="Execute raw SQL query against lte_network.db")
    parser.add_argument("--test", action="store_true", help="Run automated self-tests")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.sql:
        execute_sql(args.sql)
    elif args.generate or args.fault:
        n = args.generate if args.generate else 3
        cell = args.cell if args.cell else "CELL_102_B"
        fault = args.fault if args.fault else "CONGESTION"
        run_simulation(count=n, fault_cell=cell, fault_type=fault)
    else:
        # Default behavior: run quick sample simulation
        run_simulation(count=3, fault_cell="CELL_102_A", fault_type="CONGESTION")
