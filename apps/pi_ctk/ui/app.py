import os
import threading
import time
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox

import cv2
from PIL import Image

try:
    import customtkinter as ctk
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "customtkinter is required for PI CTk MVP. Install with: pip install customtkinter"
    ) from e

from ..core.camera_service import CameraService
from ..core.demo_service import DemoService
from ..core.inference_service import InferenceRequest, InferenceService
from ..core.storage_service import StorageService, StoredRecord


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_model_path() -> str:
    p = repo_root() / "onnx model" / "checkpoint_epoch_31.onnx"
    return str(p)


def default_demo_path() -> str:
    candidates = [
        Path(r"D:\-Users-\Documents\GitHub\model-\model-output2.html"),
        repo_root() / "HTML" / "index.html",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])


class PiCtkMvpApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MicroAI Pi MVP - Engineering Edition")
        self.geometry("1460x860")

        self.storage = StorageService()
        self.camera = CameraService()
        self.inference = InferenceService(
            model_path=default_model_path(),
            intra_threads=4,
            inter_threads=1,
        )
        self.demo = DemoService(default_demo_path())

        self._preview_image = None
        self._running = True
        self._req_ctx: dict[str, tuple[str, str, str]] = {}

        self._build_ui()
        self._start_services()
        self.after(33, self._tick_preview)
        self.after(80, self._tick_inference_result)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self)
        right = ctk.CTkFrame(self)
        left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        right.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        left.grid_rowconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=0)
        left.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(left, text="Camera Preview", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        controls = ctk.CTkFrame(left)
        controls.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        for i in range(4):
            controls.grid_columnconfigure(i, weight=1)

        self.btn_capture = ctk.CTkButton(
            controls, text="拍照并推理", command=self._on_capture
        )
        self.btn_import = ctk.CTkButton(
            controls, text="导入图片并推理", command=self._on_import_image
        )
        self.btn_usb = ctk.CTkButton(
            controls, text="USB批量导入并推理", command=self._on_import_usb
        )
        self.btn_refresh_batch = ctk.CTkButton(
            controls, text="刷新当前批次", command=self._refresh_history_box
        )
        self.btn_capture.grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        self.btn_import.grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        self.btn_usb.grid(row=0, column=2, padx=6, pady=8, sticky="ew")
        self.btn_refresh_batch.grid(row=0, column=3, padx=6, pady=8, sticky="ew")

        right.grid_rowconfigure(8, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="模型路径").grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4)
        )
        self.entry_model = ctk.CTkEntry(right)
        self.entry_model.insert(0, default_model_path())
        self.entry_model.grid(row=1, column=0, sticky="ew", padx=8)

        ctk.CTkLabel(right, text="检测参数").grid(
            row=2, column=0, sticky="w", padx=8, pady=(8, 4)
        )
        param_row = ctk.CTkFrame(right)
        param_row.grid(row=3, column=0, sticky="ew", padx=8)
        for i in range(6):
            param_row.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(param_row, text="Score").grid(row=0, column=0, padx=4)
        self.entry_thr = ctk.CTkEntry(param_row, width=72)
        self.entry_thr.insert(0, "0.45")
        self.entry_thr.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(param_row, text="NMS").grid(row=0, column=2, padx=4)
        self.entry_nms = ctk.CTkEntry(param_row, width=72)
        self.entry_nms.insert(0, "0.30")
        self.entry_nms.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(param_row, text="A阈值").grid(row=0, column=4, padx=4)
        self.entry_high_thr = ctk.CTkEntry(param_row, width=72)
        self.entry_high_thr.insert(0, "0.75")
        self.entry_high_thr.grid(row=0, column=5, padx=4, sticky="ew")

        ctk.CTkLabel(right, text="命名规范").grid(
            row=4, column=0, sticky="w", padx=8, pady=(8, 4)
        )
        naming_row = ctk.CTkFrame(right)
        naming_row.grid(row=5, column=0, sticky="ew", padx=8)
        for i in range(6):
            naming_row.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(naming_row, text="菌种").grid(row=0, column=0, padx=4)
        self.entry_strain = ctk.CTkEntry(naming_row)
        self.entry_strain.insert(0, "default_strain")
        self.entry_strain.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(naming_row, text="批次").grid(row=0, column=2, padx=4)
        self.entry_batch = ctk.CTkEntry(naming_row)
        self.entry_batch.insert(0, "batch_001")
        self.entry_batch.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(naming_row, text="时间格式").grid(row=0, column=4, padx=4)
        self.entry_timefmt = ctk.CTkEntry(naming_row)
        self.entry_timefmt.insert(0, "%Y%m%d_%H%M%S")
        self.entry_timefmt.grid(row=0, column=5, padx=4, sticky="ew")

        op_row = ctk.CTkFrame(right)
        op_row.grid(row=6, column=0, sticky="ew", padx=8, pady=(8, 0))
        for i in range(3):
            op_row.grid_columnconfigure(i, weight=1)
        self.btn_reload_model = ctk.CTkButton(
            op_row, text="重载模型", command=self._on_reload_model
        )
        self.btn_open_demo = ctk.CTkButton(
            op_row, text="打开3D演示", command=self._on_open_demo
        )
        self.btn_export = ctk.CTkButton(
            op_row, text="导出批次CSV+ZIP", command=self._on_export_report
        )
        self.btn_reload_model.grid(row=0, column=0, padx=4, pady=6, sticky="ew")
        self.btn_open_demo.grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        self.btn_export.grid(row=0, column=2, padx=4, pady=6, sticky="ew")

        self.status_label = ctk.CTkLabel(right, text="状态: 初始化中", anchor="w")
        self.status_label.grid(row=7, column=0, sticky="ew", padx=8, pady=(8, 4))

        self.history_box = ctk.CTkTextbox(right, wrap="none")
        self.history_box.grid(row=8, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self._refresh_history_box()

    def _start_services(self) -> None:
        cam_ok = self.camera.start()
        inf_ok = self.inference.start()
        self._set_status(
            f"相机: {'OK' if cam_ok else '失败'} | 推理: {'OK' if inf_ok else '失败'}"
        )

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=f"状态: {text}")

    def _safe_float(self, value: str, fallback: float) -> float:
        try:
            return float(value.strip())
        except Exception:
            return fallback

    def _ctx(self) -> tuple[str, str, str]:
        strain = self.entry_strain.get().strip() or "default_strain"
        batch = self.entry_batch.get().strip() or "batch_001"
        timefmt = self.entry_timefmt.get().strip() or "%Y%m%d_%H%M%S"
        return strain, batch, timefmt

    def _tick_preview(self) -> None:
        if not self._running:
            return
        pkt = self.camera.get_latest()
        if pkt is not None:
            rgb = cv2.cvtColor(pkt.frame_bgr, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            self._preview_image = ctk.CTkImage(
                light_image=pil, dark_image=pil, size=(940, 540)
            )
            self.preview_label.configure(image=self._preview_image, text="")
        self.after(33, self._tick_preview)

    def _tick_inference_result(self) -> None:
        if not self._running:
            return
        while True:
            result = self.inference.try_get_result()
            if result is None:
                break
            if result.error:
                self._set_status(f"推理失败: {result.error}")
                continue

            strain, batch, timefmt = self._req_ctx.pop(result.request_id, self._ctx())
            assert result.annotated_bgr is not None
            annot_path = self.storage.save_annotated(
                result.annotated_bgr, strain, batch, timefmt
            )

            rec = StoredRecord(
                timestamp=time.time(),
                strain_name=strain,
                batch_id=batch,
                source_type=result.source_type,
                source_path=result.source_path,
                annotated_path=str(annot_path),
                model_path=self.entry_model.get().strip(),
                score_threshold=self._safe_float(self.entry_thr.get(), 0.45),
                nms_iou=self._safe_float(self.entry_nms.get(), 0.30),
                high_conf_threshold=self._safe_float(self.entry_high_thr.get(), 0.75),
                count=result.count,
                high_count=result.high_count,
                low_count=result.low_count,
                latency_ms=result.latency_ms,
                top_score=result.top_score,
                avg_score=result.avg_score,
                details=result.details,
                summary_text=result.summary_text,
            )
            self.storage.append_history(rec)
            self._set_status(
                f"完成: {strain}/{batch} | total={result.count}, "
                f"A={result.high_count}, B={result.low_count}, {result.latency_ms:.1f}ms"
            )

        self._refresh_history_box()
        self.after(80, self._tick_inference_result)

    def _submit_inference_from_path(
        self, path: str, source_type: str, silent: bool = False
    ) -> bool:
        image = cv2.imread(path)
        if image is None:
            if not silent:
                messagebox.showerror("错误", f"无法读取图片: {path}")
            return False

        strain, batch, timefmt = self._ctx()
        req_id = str(uuid.uuid4())
        self._req_ctx[req_id] = (strain, batch, timefmt)
        req = InferenceRequest(
            request_id=req_id,
            source_path=path,
            source_type=source_type,
            source_bgr=image,
            threshold=self._safe_float(self.entry_thr.get(), 0.45),
            nms_iou=self._safe_float(self.entry_nms.get(), 0.30),
            high_conf_thr=self._safe_float(self.entry_high_thr.get(), 0.75),
            model_name=Path(self.entry_model.get().strip()).name,
        )
        ok = self.inference.submit(req)
        if ok:
            if not silent:
                self._set_status(f"任务已提交: {strain}/{batch}")
            return True
        self._req_ctx.pop(req_id, None)
        if not silent:
            self._set_status("推理队列繁忙，请稍后")
        return False

    def _submit_many(self, paths: list[str], source_type: str) -> None:
        def worker() -> None:
            submitted = 0
            for p in paths:
                while self._running:
                    if self._submit_inference_from_path(
                        p, source_type=source_type, silent=True
                    ):
                        submitted += 1
                        break
                    time.sleep(0.15)
            self.after(
                0,
                lambda: self._set_status(f"批量任务提交完成: {submitted}/{len(paths)}"),
            )

        threading.Thread(target=worker, name="batch-submit", daemon=True).start()

    def _on_capture(self) -> None:
        pkt = self.camera.get_latest()
        if pkt is None:
            messagebox.showwarning("提示", "当前没有可用相机帧")
            return
        strain, batch, timefmt = self._ctx()
        p = self.storage.save_capture(pkt.frame_bgr, strain, batch, timefmt)
        self._submit_inference_from_path(str(p), source_type="capture")

    def _on_import_image(self) -> None:
        f = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")],
        )
        if not f:
            return
        strain, batch, timefmt = self._ctx()
        p = self.storage.save_imported_file(f, strain, batch, timefmt)
        self._submit_inference_from_path(str(p), source_type="import")

    def _on_import_usb(self) -> None:
        initialdir = None
        for root in self.storage.default_usb_roots():
            if Path(root).exists():
                initialdir = root
                break
        folder = filedialog.askdirectory(
            title="选择USB目录", initialdir=initialdir or os.getcwd()
        )
        if not folder:
            return
        strain, batch, timefmt = self._ctx()
        imported = self.storage.import_from_usb_dir(folder, strain, batch, timefmt)
        if not imported:
            messagebox.showinfo("结果", "未在该目录找到图片")
            return
        self._submit_many([str(p) for p in imported], source_type="usb_import")
        self._set_status(f"USB已导入 {len(imported)} 张，后台排队推理中")

    def _on_reload_model(self) -> None:
        path = self.entry_model.get().strip()
        self.inference.stop()
        self.inference = InferenceService(
            model_path=path, intra_threads=4, inter_threads=1
        )
        ok = self.inference.start()
        self._set_status(f"模型重载 {'成功' if ok else '失败'}")

    def _on_open_demo(self) -> None:
        demo_path = default_demo_path()
        self.demo = DemoService(demo_path)
        ok = self.demo.open_demo()
        self._set_status("已打开3D演示" if ok else f"3D演示文件不存在: {demo_path}")

    def _on_export_report(self) -> None:
        strain, batch, timefmt = self._ctx()
        csv_path, zip_path = self.storage.export_batch_report(strain, batch, timefmt)
        self._set_status(f"已导出: {csv_path.name} + {zip_path.name}")
        messagebox.showinfo("导出完成", f"CSV:\n{csv_path}\n\nZIP:\n{zip_path}")

    def _refresh_history_box(self) -> None:
        strain, batch, _ = self._ctx()
        rows = self.storage.load_history(strain, batch, limit=120)
        self.history_box.delete("1.0", "end")
        if not rows:
            self.history_box.insert("end", f"当前批次无记录: {strain}/{batch}\n")
            return
        for r in rows:
            ts = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(r.get("timestamp", 0))
            )
            line = (
                f"{ts} | {r.get('source_type')} | total={r.get('count')} "
                f"A={r.get('high_count')} B={r.get('low_count')} "
                f"lat={r.get('latency_ms', 0):.1f}ms\n"
                f"src={r.get('source_path')}\n"
                f"ann={r.get('annotated_path')}\n"
                f"summary={r.get('summary_text')}\n\n"
            )
            self.history_box.insert("end", line)

    def on_close(self) -> None:
        self._running = False
        self.camera.stop()
        self.inference.stop()
        self.destroy()


def run() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = PiCtkMvpApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
