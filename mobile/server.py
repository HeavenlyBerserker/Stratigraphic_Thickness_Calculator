from __future__ import annotations

import argparse
import base64
import io
import json
import random
from dataclasses import asdict, is_dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable

from source.models import (
    AverageThicknessInputs,
    AverageVectorInputs,
    ConcentricFoldInputs,
    EqualAngleInputs,
    MixedAverageInputs,
    OneDipInputs,
    PlungingConcentricFoldInputs,
    TopNormalInputs,
    compute_average_thickness,
    compute_average_vector,
    compute_concentric_fold,
    compute_equal_angle,
    compute_mixed_average,
    compute_one_dip,
    compute_plunging_concentric_fold,
    compute_top_normal,
)


ModelComputeFn = Callable[[Any], Any]
InputBuilderFn = Callable[[dict[str, float]], Any]


class ModelSpec:
    def __init__(
        self,
        *,
        input_builder: InputBuilderFn,
        compute_fn: ModelComputeFn,
        field_order: list[str],
        wrap_fields: set[str],
        label: str,
        formula: list[str],
        where: list[str],
    ) -> None:
        self.input_builder = input_builder
        self.compute_fn = compute_fn
        self.field_order = field_order
        self.wrap_fields = wrap_fields
        self.label = label
        self.formula = formula
        self.where = where


MODEL_SPECS: dict[str, ModelSpec] = {
    "t1": ModelSpec(
        input_builder=lambda d: OneDipInputs(**d),
        compute_fn=compute_one_dip,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "formation_dip_deg",
            "wellbore_azimuth_deg",
            "dip_azimuth_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth_deg"},
        label="One-dip (T1)",
        formula=[
            "T1 = M(cosδ - sinδ cos(φd - φb) tanβ) cosβ",
        ],
        where=[
            "T1: one-dip true stratigraphic thickness",
            "M: measured thickness along well path",
        ],
    ),
    "t2": ModelSpec(
        input_builder=lambda d: AverageVectorInputs(**d),
        compute_fn=compute_average_vector,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Average-vector (T2)",
        formula=[
            "Uav = (Ud1 + Ud2) / ||Ud1 + Ud2||",
            "T2 = M (Uav · Ub)",
        ],
        where=["T2: average-vector thickness"],
    ),
    "t3": ModelSpec(
        input_builder=lambda d: AverageThicknessInputs(**d),
        compute_fn=compute_average_thickness,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Average-thickness (T3)",
        formula=[
            "T3 = (M Ud1·Ub + M Ud2·Ub) / 2",
            "T3 = M (Ud1 + Ud2)·Ub / 2",
        ],
        where=["T3: average-thickness model output"],
    ),
    "t4": ModelSpec(
        input_builder=lambda d: MixedAverageInputs(**d),
        compute_fn=compute_mixed_average,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Mixed Average (T4)",
        formula=["T4 = (T2 + T3) / 2"],
        where=["T4: mean of average-vector and average-thickness outputs"],
    ),
    "t5": ModelSpec(
        input_builder=lambda d: ConcentricFoldInputs(**d),
        compute_fn=compute_concentric_fold,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Concentric Fold (T5)",
        formula=[
            "β'2 = arctan(tanβ2 |cos(φd1−φd2)|)",
            "T5 = M' sinγ / cos(η/2)",
        ],
        where=["T5: concentric-fold thickness"],
    ),
    "t6": ModelSpec(
        input_builder=lambda d: PlungingConcentricFoldInputs(**d),
        compute_fn=compute_plunging_concentric_fold,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Plunging Concentric Fold (T6)",
        formula=["T6 = M' (sinγ / sinα)"],
        where=["T6: plunging-fold thickness (no base azimuth correction)"],
    ),
    "t7": ModelSpec(
        input_builder=lambda d: TopNormalInputs(**d),
        compute_fn=compute_top_normal,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Top-normal (T7)",
        formula=[
            "If S < 0: T7 = M' cos(α−η) / cosη",
            "If S ≥ 0: T7 = M' cos(α+η) / cosη",
        ],
        where=["T7: top-normal thickness"],
    ),
    "t8": ModelSpec(
        input_builder=lambda d: EqualAngleInputs(**d),
        compute_fn=compute_equal_angle,
        field_order=[
            "measured_thickness",
            "wellbore_inclination_deg",
            "wellbore_azimuth_deg",
            "formation_dip1_deg",
            "dip_azimuth1_deg",
            "formation_dip2_deg",
            "dip_azimuth2_deg",
        ],
        wrap_fields={"wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"},
        label="Equal-angle (T8)",
        formula=[
            "Top-normal intermediate from T7 branch rule",
            "T8 = Top-normal × cos(η/2)",
        ],
        where=["T8: equal-angle thickness"],
    ),
}


STATIC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STATIC_DIR.parents[1]


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _coerce_fields(raw: dict[str, Any], order: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for key in order:
        if key not in raw:
            raise ValueError(f"Missing field: {key}")
        result[key] = float(raw[key])
    return result


def _percentile(values: list[float], p: float) -> float:
    if len(values) == 1:
        return values[0]
    sorted_vals = sorted(values)
    index = (len(sorted_vals) - 1) * p
    low = int(index)
    high = min(low + 1, len(sorted_vals) - 1)
    frac = index - low
    return sorted_vals[low] * (1.0 - frac) + sorted_vals[high] * frac


def _sample_value(mu: float, sigma: float, *, wrap: bool, minimum: float, maximum: float) -> float:
    if sigma <= 0.0:
        return mu
    raw = random.gauss(mu, sigma)
    if wrap:
        width = maximum - minimum
        return ((raw - minimum) % width) + minimum
    return min(max(raw, minimum), maximum)


def _field_bounds(name: str) -> tuple[float, float]:
    if "azimuth" in name:
        return (0.0, 360.0)
    if "inclination" in name:
        return (0.0, 180.0)
    if "dip" in name:
        return (0.0, 90.0)
    return (-1_000_000.0, 1_000_000.0)


def _run_monte_carlo(
    spec: ModelSpec,
    values: dict[str, float],
    stds: dict[str, float],
    *,
    sample_count: int = 2500,
) -> dict[str, float | str] | None:
    if all(stds.get(k, 0.0) <= 1e-12 for k in spec.field_order):
        return None
    thicknesses: list[float] = []
    for _ in range(sample_count):
        sample_kwargs: dict[str, float] = {}
        for k in spec.field_order:
            lo, hi = _field_bounds(k)
            sample_kwargs[k] = _sample_value(
                values[k],
                stds.get(k, 0.0),
                wrap=k in spec.wrap_fields,
                minimum=lo,
                maximum=hi,
            )
        sample_result = spec.compute_fn(spec.input_builder(sample_kwargs))
        thicknesses.append(float(sample_result.true_stratigraphic_thickness))
    stats: dict[str, float | str] = {
        "n": float(sample_count),
        "mean": mean(thicknesses),
        "std": pstdev(thicknesses),
        "p10": _percentile(thicknesses, 0.10),
        "p25": _percentile(thicknesses, 0.25),
        "p50": _percentile(thicknesses, 0.50),
        "p75": _percentile(thicknesses, 0.75),
        "p90": _percentile(thicknesses, 0.90),
    }
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 3.5))
        if thicknesses:
            n = len(thicknesses)
            pct_weight = 100.0 / n
            ax.hist(
                thicknesses,
                bins=50,
                weights=[pct_weight] * n,
                color="#4C78A8",
                edgecolor="white",
            )
        ax.set_title(f"{spec.label} Monte Carlo Thickness Distribution")
        ax.set_xlabel("Thickness")
        ax.set_ylabel("Percentage (%)")
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=110)
        plt.close(fig)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        stats["plot_data_uri"] = f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return stats


class MobileHandler(BaseHTTPRequestHandler):
    def _write_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, filename: str, content_type: str) -> None:
        path = STATIC_DIR / filename
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/mobile"):
            self._serve_file("index.html", "text/html; charset=utf-8")
            return
        if self.path == "/logo.png":
            logo = PROJECT_ROOT / "logo.png"
            if logo.exists():
                body = logo.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if self.path == "/sw.js":
            self._serve_file("sw.js", "application/javascript; charset=utf-8")
            return
        if self.path == "/manifest.json":
            self._serve_file("manifest.json", "application/manifest+json; charset=utf-8")
            return
        if self.path == "/api/models":
            models = [
                {
                    "id": model_id,
                    "label": spec.label,
                    "fields": spec.field_order,
                    "wrap_fields": sorted(spec.wrap_fields),
                    "formula": spec.formula,
                    "where": spec.where,
                }
                for model_id, spec in MODEL_SPECS.items()
            ]
            self._write_json({"models": models})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/compute":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
            model_id = str(payload.get("model", "")).lower()
            values = payload.get("values", {})
            stds = payload.get("stds", {})
            if model_id not in MODEL_SPECS:
                raise ValueError(f"Unknown model '{model_id}'.")
            if not isinstance(values, dict):
                raise ValueError("'values' must be an object.")
            if not isinstance(stds, dict):
                raise ValueError("'stds' must be an object.")

            spec = MODEL_SPECS[model_id]
            coerced = _coerce_fields(values, spec.field_order)
            coerced_stds = {k: float(stds.get(k, 0.0)) for k in spec.field_order}
            result = spec.compute_fn(spec.input_builder(coerced))
            monte_carlo = _run_monte_carlo(spec, coerced, coerced_stds, sample_count=2500)
            self._write_json(
                {
                    "ok": True,
                    "model": model_id,
                    "result": result,
                    "inputs": coerced,
                    "stds": coerced_stds,
                    "formula": spec.formula,
                    "where": spec.where,
                    "monte_carlo": monte_carlo,
                }
            )
        except Exception as exc:  # pragma: no cover - runtime request errors
            self._write_json(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )


def run_server(host: str = "0.0.0.0", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), MobileHandler)
    print(f"Mobile PWA server running at http://{host}:{port}")
    print("Open http://localhost:8787 on PC, or http://<your-lan-ip>:8787 on phone.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mobile server...")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mobile PWA server")
    parser.add_argument("--host", default="0.0.0.0", help="Host bind address")
    parser.add_argument("--port", type=int, default=8787, help="Port number")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

