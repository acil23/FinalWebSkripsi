"""Boundary layer untuk halaman utama alur penjadwalan."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO, StringIO
import csv
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile

from app.controllers.scheduling_controller import SchedulingController
from app.core.paths import TEMPLATE_DIR
from app.services.data_loader_service import UploadedCsvPayload
from app.schemas.upload_schema import CANONICAL_FILENAMES, REQUIRED_COLUMNS, UPLOAD_DATASETS

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
controller = SchedulingController()


def _alert_query(alert_type: str, title: str, message: str) -> str:
    return f"alert_type={quote(alert_type)}&alert_title={quote(title)}&alert_message={quote(message)}"


def _read_alert_from_query(request: Request) -> dict | None:
    alert_type = request.query_params.get("alert_type")
    if not alert_type:
        return None
    return {
        "type": alert_type,
        "title": request.query_params.get("alert_title", "Informasi"),
        "message": request.query_params.get("alert_message", ""),
    }


def _csv_template_bytes(columns: list[str]) -> bytes:
    """Bangun template CSV sederhana berisi header kolom wajib."""
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    return buffer.getvalue().encode("utf-8-sig")


def _safe_download_filename(filename: str) -> str:
    return filename.replace(" ", "_").replace("/", "_")


@router.get("/templates/{dataset_key}")
def download_csv_template(dataset_key: str):
    """Mengunduh template CSV untuk setiap field upload data masukan."""
    template_map = {
        "data_dosen": (CANONICAL_FILENAMES["data_dosen"], REQUIRED_COLUMNS["data_dosen"]),
        "data_preferensi_dosen": (CANONICAL_FILENAMES["data_preferensi_dosen"], REQUIRED_COLUMNS["data_preferensi_dosen"]),
        "data_ruang_kelas": (CANONICAL_FILENAMES["data_ruang_kelas"], REQUIRED_COLUMNS["data_ruang_kelas"]),
        "data_slot_waktu": (CANONICAL_FILENAMES["data_slot_waktu"], REQUIRED_COLUMNS["data_slot_waktu"]),
        "data_jumlah_mahasiswa": (CANONICAL_FILENAMES["data_jumlah_mahasiswa"], REQUIRED_COLUMNS["data_jumlah_mahasiswa"]),
        "data_prakrs": (CANONICAL_FILENAMES["data_prakrs"], REQUIRED_COLUMNS["data_prakrs"]),
    }

    if dataset_key == "data_mata_kuliah":
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w", compression=ZIP_DEFLATED) as zip_file:
            zip_file.writestr(CANONICAL_FILENAMES["mk_wajib"], _csv_template_bytes(REQUIRED_COLUMNS["mk_wajib"]))
            zip_file.writestr(CANONICAL_FILENAMES["mk_pilihan"], _csv_template_bytes(REQUIRED_COLUMNS["mk_pilihan"]))
        zip_buffer.seek(0)
        headers = {"Content-Disposition": "attachment; filename=Template_Data_Mata_Kuliah.zip"}
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)

    if dataset_key not in template_map:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan.")

    filename, columns = template_map[dataset_key]
    download_name = _safe_download_filename(f"Template_{filename}")
    headers = {"Content-Disposition": f"attachment; filename={download_name}"}
    return StreamingResponse(BytesIO(_csv_template_bytes(columns)), media_type="text/csv", headers=headers)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    context = controller.get_dashboard_context()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "active_menu": "Dashboard",
            **context,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_alias(request: Request):
    context = controller.get_dashboard_context()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "active_menu": "Dashboard",
            **context,
        },
    )


@router.get("/unggah-data", response_class=HTMLResponse)
def upload_data_page(request: Request):
    context = controller.get_upload_page_context()
    return templates.TemplateResponse(
        "unggah_data.html",
        {"request": request, "active_menu": "Unggah Data", **context},
    )


def _has_uploaded_file(file: UploadFile | None) -> bool:
    return bool(file and file.filename)


async def _payload_from_upload(file: UploadFile) -> UploadedCsvPayload:
    content = await file.read()
    return UploadedCsvPayload(filename=file.filename or "", content=content)


@router.post("/api/upload", response_class=HTMLResponse)
async def upload_data(
    request: Request,
    data_mata_kuliah: list[UploadFile] = File(default=[]),
    data_dosen: UploadFile | None = File(default=None),
    data_preferensi_dosen: UploadFile | None = File(default=None),
    data_ruang_kelas: UploadFile | None = File(default=None),
    data_slot_waktu: UploadFile | None = File(default=None),
    data_jumlah_mahasiswa: UploadFile | None = File(default=None),
    data_prakrs: UploadFile | None = File(default=None),
):
    """Endpoint UC-01 untuk mengunggah dan memvalidasi data masukan CSV."""
    payloads: dict[str, list[UploadedCsvPayload]] = {
        "data_mata_kuliah": [],
        "data_dosen": [],
        "data_preferensi_dosen": [],
        "data_ruang_kelas": [],
        "data_slot_waktu": [],
        "data_jumlah_mahasiswa": [],
        "data_prakrs": [],
    }

    for file in data_mata_kuliah:
        if _has_uploaded_file(file):
            payloads["data_mata_kuliah"].append(await _payload_from_upload(file))

    single_files = {
        "data_dosen": data_dosen,
        "data_preferensi_dosen": data_preferensi_dosen,
        "data_ruang_kelas": data_ruang_kelas,
        "data_slot_waktu": data_slot_waktu,
        "data_jumlah_mahasiswa": data_jumlah_mahasiswa,
        "data_prakrs": data_prakrs,
    }
    for key, file in single_files.items():
        if _has_uploaded_file(file):
            payloads[key].append(await _payload_from_upload(file))

    dataset = controller.upload_data(payloads)
    if dataset.is_valid():
        alert = {
            "type": "success",
            "title": "Berhasil!",
            "message": "Data masukan berhasil divalidasi.",
        }
    else:
        alert = {
            "type": "error",
            "title": "Gagal!",
            "message": "Masih terdapat data yang belum lengkap atau struktur file yang tidak sesuai.",
        }

    context = controller.get_upload_page_context(alert=alert)
    return templates.TemplateResponse(
        "unggah_data.html",
        {"request": request, "active_menu": "Unggah Data", **context},
    )


@router.get("/konfigurasi-kelas", response_class=HTMLResponse)
def class_opening_page(
    request: Request,
    semester_active: str = Query(default="Ganjil"),
    jenis_mk: str = Query(default="Semua"),
    search: str = Query(default=""),
):
    context = controller.get_class_opening_page_context(
        semester_active=semester_active,
        jenis_mk=jenis_mk,
        search=search,
    )
    return templates.TemplateResponse(
        "konfigurasi_kelas.html",
        {"request": request, "active_menu": "Konfigurasi Kelas", **context},
    )


@router.post("/api/class-opening/generate", response_class=HTMLResponse)
async def generate_class_opening(
    request: Request,
    semester_active: str = Query(default="Ganjil"),
):
    try:
        controller.generate_class_opening(semester_active=semester_active)
        alert = {
            "type": "success",
            "title": "Berhasil!",
            "message": "Rekomendasi pembukaan kelas berhasil dibentuk.",
        }
    except Exception as exc:
        alert = {
            "type": "error",
            "title": "Gagal!",
            "message": str(exc),
        }
    context = controller.get_class_opening_page_context(semester_active=semester_active, alert=alert)
    return templates.TemplateResponse(
        "konfigurasi_kelas.html",
        {"request": request, "active_menu": "Konfigurasi Kelas", **context},
    )


@router.post("/api/class-opening/update", response_class=HTMLResponse)
async def update_class_opening(
    request: Request,
    semester_active: str = Query(default="Ganjil"),
):
    form = await request.form()
    success = controller.update_class_opening(dict(form), semester_active=semester_active)
    if success:
        alert = {
            "type": "success",
            "title": "Berhasil!",
            "message": "Konfigurasi pembukaan kelas berhasil disimpan dan sesi perkuliahan telah terbentuk.",
        }
    else:
        alert = {
            "type": "error",
            "title": "Gagal!",
            "message": "Terdapat jumlah kelas final yang tidak valid.",
        }
    context = controller.get_class_opening_page_context(semester_active=semester_active, alert=alert)
    return templates.TemplateResponse(
        "konfigurasi_kelas.html",
        {"request": request, "active_menu": "Konfigurasi Kelas", **context},
    )


@router.get("/parameter-algoritma", response_class=HTMLResponse)
def parameter_page(request: Request):
    context = controller.get_parameter_page_context()
    return templates.TemplateResponse(
        "parameter_algoritma.html",
        {"request": request, "active_menu": "Parameter Algoritma", **context},
    )


@router.post("/api/parameters", response_class=HTMLResponse)
async def save_parameters(request: Request):
    form = await request.form()
    parameter = controller.save_parameters(dict(form))
    if parameter.is_valid():
        alert = {
            "type": "success",
            "title": "Berhasil!",
            "message": "Parameter algoritma berhasil disimpan.",
        }
    else:
        alert = {
            "type": "error",
            "title": "Terdapat parameter tidak valid.",
            "message": "Silakan perbaiki nilai yang tidak valid sebelum melanjutkan.",
        }
    context = controller.get_parameter_page_context(draft_parameter=parameter, alert=alert)
    return templates.TemplateResponse(
        "parameter_algoritma.html",
        {"request": request, "active_menu": "Parameter Algoritma", **context},
    )


@router.get("/eksekusi-penjadwalan", response_class=HTMLResponse)
def execution_page(request: Request):
    alert = _read_alert_from_query(request)
    context = controller.get_execution_page_context(alert=alert)
    return templates.TemplateResponse(
        "eksekusi_penjadwalan.html",
        {"request": request, "active_menu": "Eksekusi Penjadwalan", **context},
    )


@router.post("/api/scheduling/execute")
async def execute_scheduling(request: Request):
    """Memulai eksekusi.

    Jalur browser biasa memakai redirect 303 agar Firefox/Chrome tidak memunculkan
    dialog resend form saat halaman di-refresh otomatis. Jalur JavaScript/fetch
    menerima JSON supaya halaman dapat mulai polling tanpa navigasi halaman.
    """
    is_fetch_request = request.headers.get("x-requested-with") == "fetch"
    try:
        controller.start_scheduling_execution()
    except Exception as exc:
        if is_fetch_request:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": str(exc)},
            )
        query = _alert_query("error", "Eksekusi gagal dimulai", str(exc))
        return RedirectResponse(url=f"/eksekusi-penjadwalan?{query}", status_code=303)

    message = "Proses penjadwalan sedang berjalan. Halaman akan memperbarui status secara berkala."
    if is_fetch_request:
        return {"ok": True, "message": message}
    query = _alert_query("success", "Eksekusi dimulai", message)
    return RedirectResponse(url=f"/eksekusi-penjadwalan?{query}", status_code=303)


@router.get("/api/scheduling/status")
def scheduling_status():
    result = controller.get_current_result()
    return {
        "status": controller.get_execution_page_context().get("execution_status"),
        "has_result": bool(result and result.is_ready_to_display()),
        "summary": result.to_summary() if result and result.is_ready_to_display() else None,
    }


@router.get("/hasil-penjadwalan", response_class=HTMLResponse)
def result_page(request: Request):
    alert = None
    alert_type = request.query_params.get("alert_type")
    if alert_type:
        alert = {
            "type": alert_type,
            "title": request.query_params.get("alert_title", "Informasi"),
            "message": request.query_params.get("alert_message", ""),
        }
    context = controller.get_result_page_context(alert=alert)
    return templates.TemplateResponse(
        "hasil_penjadwalan.html",
        {"request": request, "active_menu": "Hasil Penjadwalan", **context},
    )


@router.get("/api/scheduling/result")
def scheduling_result():
    return controller.get_result_api_data()
