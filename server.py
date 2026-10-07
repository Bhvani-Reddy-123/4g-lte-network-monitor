#!/usr/bin/env python3
"""
4G LTE Network Monitoring, Fault Detection & RCA Web Dashboard Server
Author: Antigravity AI Team
Description: Full-stack Python HTTP server serving NOC dashboard & REST API for live telemetry,
             RCA diagnostic solver, fault injection engine, and SQLite query runner.
"""

import sys
import os
import json
import sqlite3
import random
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime

# Import core LTE engine
import lte_engine

# Fix Windows stdout encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
if not os.path.exists(PUBLIC_DIR):
    os.makedirs(PUBLIC_DIR)

# Global State
active_faults = {
    "CELL_102_B": "CONGESTION",
    "CELL_105_C": "INTERFERENCE",
    "CELL_108_A": "SITE_OUTAGE"
}
latest_telemetry_map = {}
alarm_logs = []
custom_thresholds = dict(lte_engine.THRESHOLDS)

def background_telemetry_loop():
    """Continuously generates telemetry every 2 seconds, runs RCA, and persists to SQLite."""
    lte_engine.init_db()
    
    while True:
        timestamp = datetime.now().isoformat()
        new_map = {}

        for cell in lte_engine.CELLS:
            cid = cell["cell_id"]
            f_override = active_faults.get(cid)
            telem = lte_engine.generate_cell_telemetry(cell, fault_override=f_override)
            new_map[cid] = telem

            # Perform RCA check
            alarm = lte_engine.perform_root_cause_analysis(telem)
            if alarm:
                # Add confidence score & symptom matrix for rich web dashboard
                alarm["confidence_percent"] = 96 if alarm["category"] == "SITE_OUTAGE" else 92
                alarm["id"] = f"ALM_{cid}_{int(time.time()*1000)}"
                
                # Check if alarm already active in list
                existing = next((a for a in alarm_logs if a["cell_id"] == cid and a["status"] == "ACTIVE"), None)
                if not existing:
                    alarm_logs.insert(0, alarm)
                else:
                    existing["evidence"] = alarm["evidence"]

            lte_engine.save_to_db(telem, alarm)

        latest_telemetry_map.update(new_map)
        time.sleep(2.0)

# Start background thread
bg_thread = threading.Thread(target=background_telemetry_loop, daemon=True)
bg_thread.start()

class NOCRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path_without_query = path.split('?')[0]
        if path_without_query == "/" or path_without_query == "/index.html":
            return os.path.join(PUBLIC_DIR, "index.html")
        return super().translate_path(path)

    def do_GET(self):
        url_path = self.path.split('?')[0]
        
        if url_path == "/api/telemetry":
            self.send_json_response({
                "cells": lte_engine.CELLS,
                "telemetry": latest_telemetry_map,
                "active_faults": active_faults
            })
        elif url_path == "/api/alarms":
            self.send_json_response({
                "alarms": alarm_logs
            })
        elif url_path == "/api/thresholds":
            self.send_json_response({
                "thresholds": custom_thresholds
            })
        else:
            super().do_GET()

    def do_POST(self):
        url_path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data) if post_data else {}

        if url_path == "/api/fault":
            cell_id = data.get("cell_id")
            fault = data.get("fault")
            if cell_id:
                if fault == "NORMAL" or not fault:
                    if cell_id in active_faults:
                        del active_faults[cell_id]
                    # Mark existing active alarms as RESOLVED
                    for a in alarm_logs:
                        if a["cell_id"] == cell_id and a["status"] == "ACTIVE":
                            a["status"] = "RESOLVED"
                else:
                    active_faults[cell_id] = fault
            self.send_json_response({"status": "success", "active_faults": active_faults})

        elif url_path == "/api/mitigate":
            alarm_id = data.get("alarm_id")
            for a in alarm_logs:
                if a["id"] == alarm_id or a["cell_id"] == data.get("cell_id"):
                    a["status"] = "RESOLVED"
                    cid = a["cell_id"]
                    if cid in active_faults:
                        del active_faults[cid]
            self.send_json_response({"status": "mitigated"})

        elif url_path == "/api/sql":
            query = data.get("query", "")
            try:
                conn = sqlite3.connect(lte_engine.DB_FILE)
                cursor = conn.cursor()
                t0 = time.time()
                cursor.execute(query)
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description] if cursor.description else []
                exec_time = round((time.time() - t0) * 1000, 2)
                conn.close()
                self.send_json_response({
                    "status": "success",
                    "columns": cols,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time_ms": exec_time
                })
            except Exception as e:
                self.send_json_response({"status": "error", "message": str(e)}, code=400)

        elif url_path == "/api/thresholds":
            new_t = data.get("thresholds", {})
            custom_thresholds.update(new_t)
            lte_engine.THRESHOLDS.update(new_t)
            self.send_json_response({"status": "updated", "thresholds": custom_thresholds})

        else:
            self.send_error(404, "Endpoint not found")

    def send_json_response(self, data_dict, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data_dict).encode('utf-8'))

def run_server():
    print(f"\n========================================================")
    print(f"🚀 4G LTE NOC MONITORING & RCA DASHBOARD SERVER ONLINE")
    print(f"========================================================")
    print(f"📡 Serving Web Dashboard: http://localhost:{PORT}")
    print(f"📁 Database File:         {lte_engine.DB_FILE}")
    print(f"Press Ctrl+C to stop server.\n")

    httpd = HTTPServer(('0.0.0.0', PORT), NOCRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NOC Server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
