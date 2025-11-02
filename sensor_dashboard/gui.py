"""Tkinter-based dashboard for displaying sensor readings."""

from __future__ import annotations

import json
import logging
import tkinter as tk
from queue import Empty
from tkinter import ttk
from typing import Dict

from .config import GUI_REFRESH_INTERVAL_MS
from .manager import SensorManager, SensorUpdate
from .sensors import SensorReading

LOGGER = logging.getLogger(__name__)


class SensorDashboardApp:
    """Render live sensor updates in a desktop GUI."""

    def __init__(self, manager: SensorManager) -> None:
        self._manager = manager
        self._root = tk.Tk()
        self._root.title("Open Sensor Dashboard")
        self._root.geometry("1000x600")
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._tree = ttk.Treeview(
            self._root,
            columns=("category", "timestamp", "status", "summary"),
            show="headings",
        )
        self._tree.heading("category", text="Category")
        self._tree.heading("timestamp", text="Last update (UTC)")
        self._tree.heading("status", text="Status")
        self._tree.heading("summary", text="Summary")
        self._tree.column("category", width=120, anchor=tk.W)
        self._tree.column("timestamp", width=180, anchor=tk.W)
        self._tree.column("status", width=100, anchor=tk.W)
        self._tree.column("summary", width=580, anchor=tk.W)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        self._detail = tk.Text(self._root, height=12)
        self._detail.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self._detail.configure(state=tk.DISABLED)

        self._rows: Dict[str, str] = {}
        self._latest: Dict[str, SensorReading] = {}

    def run(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self._manager.start()
        self._schedule_queue_drain()
        self._root.mainloop()

    def _schedule_queue_drain(self) -> None:
        self._process_queue()
        self._root.after(GUI_REFRESH_INTERVAL_MS, self._schedule_queue_drain)

    def _process_queue(self) -> None:
        queue = self._manager.queue
        while True:
            try:
                update = queue.get_nowait()
            except Empty:
                break
            self._update_sensor(update)

    def _update_sensor(self, update: SensorUpdate) -> None:
        reading = update.reading
        sensor = update.sensor
        timestamp = reading.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        summary = self._summarize_values(reading)
        status = reading.status
        item_id = self._rows.get(sensor.name)
        values = (sensor.category, timestamp, status, summary)
        if item_id is None:
            item_id = self._tree.insert("", tk.END, iid=sensor.name, values=values, text=sensor.name)
            self._rows[sensor.name] = item_id
        else:
            self._tree.item(item_id, values=values)
        self._latest[sensor.name] = reading
        if self._tree.selection() == (item_id,):
            self._render_detail(sensor.name)

    def _summarize_values(self, reading: SensorReading) -> str:
        if reading.message:
            return reading.message
        parts = []
        for key, value in reading.values.items():
            if isinstance(value, list):
                parts.append(f"{key}: {len(value)} entries")
            elif isinstance(value, dict):
                parts.append(f"{key}: {json.dumps(value)}")
            else:
                parts.append(f"{key}: {value}")
        return "; ".join(parts) if parts else "No data"

    def _render_detail(self, sensor_name: str) -> None:
        reading = self._latest.get(sensor_name)
        if not reading:
            return
        self._detail.configure(state=tk.NORMAL)
        self._detail.delete("1.0", tk.END)
        detail_payload = {
            "timestamp": reading.timestamp.isoformat(),
            "status": reading.status,
            "message": reading.message,
            "values": reading.values,
            "raw": reading.raw,
        }
        self._detail.insert(tk.END, json.dumps(detail_payload, indent=2, default=str))
        self._detail.configure(state=tk.DISABLED)

    def _on_select(self, event: tk.Event | None = None) -> None:
        selection = self._tree.selection()
        if selection:
            self._render_detail(selection[0])

    def _on_close(self) -> None:
        try:
            self._manager.stop()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to stop manager cleanly: %s", exc)
        self._root.destroy()
