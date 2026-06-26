"""State sementara aplikasi.

State ini menjaga data aktif selama server berjalan, meliputi dataset, parameter,
konfigurasi pembukaan kelas, kelas, sesi, hasil penjadwalan, dan status eksekusi.
State in-memory ini digunakan untuk mendukung alur single-admin sesuai ruang
lingkup implementasi sistem.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    current_dataset: Any | None = None
    current_parameter: Any | None = None
    current_class_opening: Any | None = None
    current_classes: Any | None = None
    current_sessions: Any | None = None
    current_result: Any | None = None
    execution_status: dict[str, Any] = field(default_factory=dict)


app_state = AppState()
