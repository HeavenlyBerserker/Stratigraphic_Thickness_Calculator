from __future__ import annotations

import base64
import io
import random
import sys
from statistics import mean, pstdev
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QToolButton

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
from source.theme import DARK_STYLESHEET, LIGHT_STYLESHEET
from source.widgets import ModelTab


class StratigraphicCalculatorWindow(QMainWindow):
    def __init__(self, initial_dark: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("Stratigraphic Thickness Calculator")
        self.resize(1200, 800)
        self._set_window_logo()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_tabs()
        self._dark_mode = initial_dark
        self._setup_theme_toggle()
        self._sync_all_model_tab_themes()

    def _setup_theme_toggle(self) -> None:
        self._theme_toggle_btn = QToolButton(self)
        self._theme_toggle_btn.setObjectName("themeToggle")
        self._theme_toggle_btn.setFixedSize(40, 28)
        self._theme_toggle_btn.setAutoRaise(True)
        self._theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self._theme_toggle_btn.font()
        font.setPointSize(14)
        self._theme_toggle_btn.setFont(font)
        self._update_theme_toggle_button()
        self._theme_toggle_btn.clicked.connect(self._toggle_theme)
        self.statusBar().addPermanentWidget(self._theme_toggle_btn)

    def _update_theme_toggle_button(self) -> None:
        # Moon while in light mode → switch to dark; sun while in dark → switch to light.
        if self._dark_mode:
            self._theme_toggle_btn.setText("\u2600")
            self._theme_toggle_btn.setToolTip("Switch to light theme")
        else:
            self._theme_toggle_btn.setText("\u263e")
            self._theme_toggle_btn.setToolTip("Switch to dark theme")

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(DARK_STYLESHEET if self._dark_mode else LIGHT_STYLESHEET)
        self._update_theme_toggle_button()
        self._sync_all_model_tab_themes()

    def _sync_all_model_tab_themes(self) -> None:
        for idx in range(self.tabs.count()):
            w = self.tabs.widget(idx)
            if isinstance(w, ModelTab):
                w.apply_theme(self._dark_mode)

    def _set_window_logo(self) -> None:
        if getattr(sys, "frozen", False):
            base_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        else:
            base_dir = Path(__file__).resolve().parent.parent
        icon_path = base_dir / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _build_tabs(self) -> None:
        one_dip_tab = ModelTab(
            "One-dip (T₁) Model", self._compute_one_dip, "One-dip (T₁)"
        )
        one_dip_tab.add_float_input(
            "m",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        one_dip_tab.add_float_input(
            "delta",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        one_dip_tab.add_float_input(
            "beta1",
            "β<sub>1</sub> (Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        one_dip_tab.add_float_input(
            "phib",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        one_dip_tab.add_float_input(
            "phid1",
            "φ<sub>d1</sub> (Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        self.tabs.addTab(one_dip_tab, "One-dip (T₁)")

        average_vector_tab = ModelTab(
            "Average-vector (T₂) Model",
            self._compute_average_vector,
            "Average-vector (T₂)",
        )
        average_vector_tab.add_float_input(
            "m2",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        average_vector_tab.add_float_input(
            "delta2",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        average_vector_tab.add_float_input(
            "phib2",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        average_vector_tab.add_float_input(
            "beta1_2",
            "β<sub>1</sub> (Upper Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        average_vector_tab.add_float_input(
            "phid1_2",
            "φ<sub>d1</sub> (Upper Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        average_vector_tab.add_float_input(
            "beta2_2",
            "β<sub>2</sub> (Lower Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        average_vector_tab.add_float_input(
            "phid2_2",
            "φ<sub>d2</sub> (Lower Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(average_vector_tab, "Average-vector (T₂)")
        average_thickness_tab = ModelTab(
            "Average-thickness (T₃) Model",
            self._compute_average_thickness,
            "Average-thickness (T₃)",
        )
        average_thickness_tab.add_float_input(
            "m3",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        average_thickness_tab.add_float_input(
            "delta3",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        average_thickness_tab.add_float_input(
            "phib3",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        average_thickness_tab.add_float_input(
            "beta1_3",
            "β<sub>1</sub> (Upper Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        average_thickness_tab.add_float_input(
            "phid1_3",
            "φ<sub>d1</sub> (Upper Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        average_thickness_tab.add_float_input(
            "beta2_3",
            "β<sub>2</sub> (Lower Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        average_thickness_tab.add_float_input(
            "phid2_3",
            "φ<sub>d2</sub> (Lower Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(average_thickness_tab, "Average-thickness (T₃)")
        mixed_average_tab = ModelTab(
            "Mixed Average (T₄) Model",
            self._compute_mixed_average,
            "Mixed Average (T₄)",
        )
        mixed_average_tab.add_float_input(
            "m4",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        mixed_average_tab.add_float_input(
            "delta4",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        mixed_average_tab.add_float_input(
            "phib4",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        mixed_average_tab.add_float_input(
            "beta1_4",
            "β<sub>1</sub> (Upper Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        mixed_average_tab.add_float_input(
            "phid1_4",
            "φ<sub>d1</sub> (Upper Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        mixed_average_tab.add_float_input(
            "beta2_4",
            "β<sub>2</sub> (Lower Formation Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        mixed_average_tab.add_float_input(
            "phid2_4",
            "φ<sub>d2</sub> (Lower Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(mixed_average_tab, "Mixed Average (T₄)")
        concentric_fold_tab = ModelTab(
            "Concentric Fold (T₅) Model",
            self._compute_concentric_fold,
            "Concentric Fold (T₅)",
        )
        concentric_fold_tab.add_float_input(
            "m5",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        concentric_fold_tab.add_float_input(
            "delta5",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        concentric_fold_tab.add_float_input(
            "phib5",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        concentric_fold_tab.add_float_input(
            "beta1_5",
            "β<sub>1</sub> (Top Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        concentric_fold_tab.add_float_input(
            "phid1_5",
            "φ<sub>d1</sub> (Top Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        concentric_fold_tab.add_float_input(
            "beta2_5",
            "β<sub>2</sub> (Base Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        concentric_fold_tab.add_float_input(
            "phid2_5",
            "φ<sub>d2</sub> (Base Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(concentric_fold_tab, "Concentric Fold (T₅)")
        plunging_fold_tab = ModelTab(
            "Plunging Concentric Fold (T₆) Model",
            self._compute_plunging_concentric_fold,
            "Plunging Concentric Fold (T₆)",
        )
        plunging_fold_tab.add_float_input(
            "m6",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        plunging_fold_tab.add_float_input(
            "delta6",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        plunging_fold_tab.add_float_input(
            "phib6",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        plunging_fold_tab.add_float_input(
            "beta1_6",
            "β<sub>1</sub> (Top Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        plunging_fold_tab.add_float_input(
            "phid1_6",
            "φ<sub>d1</sub> (Top Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        plunging_fold_tab.add_float_input(
            "beta2_6",
            "β<sub>2</sub> (Base Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        plunging_fold_tab.add_float_input(
            "phid2_6",
            "φ<sub>d2</sub> (Base Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(plunging_fold_tab, "Plunging Concentric Fold (T₆)")

        top_normal_tab = ModelTab(
            "Top-normal (T₇) Model", self._compute_top_normal, "Top-normal (T₇)"
        )
        top_normal_tab.add_float_input(
            "m7",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        top_normal_tab.add_float_input(
            "delta7",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        top_normal_tab.add_float_input(
            "phib7",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        top_normal_tab.add_float_input(
            "beta1_7",
            "β<sub>1</sub> (Top Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        top_normal_tab.add_float_input(
            "phid1_7",
            "φ<sub>d1</sub> (Top Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        top_normal_tab.add_float_input(
            "beta2_7",
            "β<sub>2</sub> (Base Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        top_normal_tab.add_float_input(
            "phid2_7",
            "φ<sub>d2</sub> (Base Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(top_normal_tab, "Top-normal (T₇)")

        equal_angle_tab = ModelTab(
            "Equal-angle (T₈) Model", self._compute_equal_angle, "Equal-angle (T₈)"
        )
        equal_angle_tab.add_float_input(
            "m8",
            "M (Measured Thickness)",
            minimum=0.0,
            default=100.0,
            step=1.0,
        )
        equal_angle_tab.add_float_input(
            "delta8",
            "δ (Wellbore Inclination, deg)",
            minimum=0.0,
            maximum=90.0,
            default=20.0,
        )
        equal_angle_tab.add_float_input(
            "phib8",
            "φ<sub>b</sub> (Wellbore Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=120.0,
        )
        equal_angle_tab.add_float_input(
            "beta1_8",
            "β<sub>1</sub> (Top Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=15.0,
        )
        equal_angle_tab.add_float_input(
            "phid1_8",
            "φ<sub>d1</sub> (Top Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=140.0,
        )
        equal_angle_tab.add_float_input(
            "beta2_8",
            "β<sub>2</sub> (Base Dip, deg)",
            minimum=0.0,
            maximum=89.99,
            default=18.0,
        )
        equal_angle_tab.add_float_input(
            "phid2_8",
            "φ<sub>d2</sub> (Base Dip Azimuth, deg)",
            minimum=0.0,
            maximum=360.0,
            default=150.0,
        )
        self.tabs.addTab(equal_angle_tab, "Equal-angle (T₈)")

        self._wire_monte_carlo_export_on_tabs()

    def _wire_monte_carlo_export_on_tabs(self) -> None:
        for idx in range(self.tabs.count()):
            w = self.tabs.widget(idx)
            if isinstance(w, ModelTab):
                w.mc_save_fn = self._save_monte_carlo_figure_file

    def _apply_model_output(
        self,
        tab: ModelTab,
        output_html: str,
        mc_stats: dict[str, float | str | list[float]] | None,
        xlsx_input_columns: list[tuple[str, float, float]],
        xlsx_output_rows: list[tuple[str, float | int]],
        xlsx_mc_rows: list[tuple[str, float | int]] | None,
    ) -> None:
        tab.set_output(output_html, is_html=True)
        if mc_stats is not None and mc_stats.get("thicknesses"):
            tab.set_monte_carlo_export_state(
                list(mc_stats["thicknesses"]),
                str(mc_stats.get("plot_title", "")),
            )
        tab.set_export_snapshot_sections(
            xlsx_input_columns,
            xlsx_output_rows,
            xlsx_mc_rows,
        )

    @staticmethod
    def _xlsx_input_column(
        tab: ModelTab, input_key: str, column_name: str
    ) -> tuple[str, float, float]:
        return (column_name, tab.value(input_key), tab.std(input_key))

    @staticmethod
    def _vec3_csv_rows(
        prefix: str, v: tuple[float, float, float]
    ) -> list[tuple[str, float]]:
        return [
            (f"{prefix}_x", v[0]),
            (f"{prefix}_y", v[1]),
            (f"{prefix}_z", v[2]),
        ]

    @staticmethod
    def _mc_excel_rows_from_stats(
        mc_stats: dict[str, float | str | list[float]] | None,
    ) -> list[tuple[str, float | int]] | None:
        if mc_stats is None:
            return None
        return [
            ("MC_N", int(mc_stats["n"])),
            ("MC_mean", float(mc_stats["mean"])),
            ("MC_std", float(mc_stats["std"])),
            ("MC_P10", float(mc_stats["p10"])),
            ("MC_P25", float(mc_stats["p25"])),
            ("MC_P50", float(mc_stats["p50"])),
            ("MC_P75", float(mc_stats["p75"])),
            ("MC_P90", float(mc_stats["p90"])),
        ]

    def _percentile(self, values: list[float], p: float) -> float:
        if not values:
            raise ValueError("Cannot compute percentile on empty values.")
        if len(values) == 1:
            return values[0]
        sorted_vals = sorted(values)
        index = (len(sorted_vals) - 1) * p
        low = int(index)
        high = min(low + 1, len(sorted_vals) - 1)
        frac = index - low
        return sorted_vals[low] * (1.0 - frac) + sorted_vals[high] * frac

    def _any_std_non_zero(self, tab: ModelTab, keys: list[str]) -> bool:
        return any(tab.std(key) > 1e-12 for key in keys)

    def _sample_values(
        self,
        tab: ModelTab,
        key: str,
        sample_count: int,
        wrap: bool = False,
    ) -> list[float]:
        mu = tab.value(key)
        sigma = tab.std(key)
        if sigma <= 0.0:
            return [mu] * sample_count

        minimum = tab.inputs[key].minimum()
        maximum = tab.inputs[key].maximum()
        sampled: list[float] = []
        adjusted = 0
        if wrap:
            width = maximum - minimum
            for _ in range(sample_count):
                raw = random.gauss(mu, sigma)
                wrapped = ((raw - minimum) % width) + minimum
                if abs(wrapped - raw) > 1e-12:
                    adjusted += 1
                sampled.append(wrapped)
            print(f"{key}: wrap-around applied to {adjusted} Monte Carlo samples.")
            return sampled

        for _ in range(sample_count):
            raw = random.gauss(mu, sigma)
            clipped = min(max(raw, minimum), maximum)
            if abs(clipped - raw) > 1e-12:
                adjusted += 1
            sampled.append(clipped)
        print(f"{key}: truncation applied to {adjusted} Monte Carlo samples.")
        return sampled

    def _run_monte_carlo(
        self,
        tab: ModelTab,
        key_to_field: list[tuple[str, str]],
        wrap_keys: set[str],
        compute_fn,
        sample_count: int = 10000,
    ) -> dict[str, float | str] | None:
        keys = [key for key, _ in key_to_field]
        if not self._any_std_non_zero(tab, keys):
            return None

        print(f"Monte Carlo enabled: running {sample_count} simulations...")
        sampled_by_key = {
            key: self._sample_values(
                tab,
                key,
                sample_count,
                wrap=key in wrap_keys,
            )
            for key in keys
        }

        thicknesses: list[float] = []
        for idx in range(sample_count):
            kwargs = {
                field: sampled_by_key[key][idx]
                for key, field in key_to_field
            }
            result = compute_fn(**kwargs)
            thicknesses.append(result.true_stratigraphic_thickness)

        plot_title = (
            f"{self.tabs.tabText(self.tabs.currentIndex())} "
            "Monte Carlo Thickness Distribution"
        )
        plot_html = self._build_monte_carlo_plot_html(thicknesses, plot_title)
        return {
            "n": float(len(thicknesses)),
            "mean": mean(thicknesses),
            "std": pstdev(thicknesses),
            "p10": self._percentile(thicknesses, 0.10),
            "p25": self._percentile(thicknesses, 0.25),
            "p50": self._percentile(thicknesses, 0.50),
            "p75": self._percentile(thicknesses, 0.75),
            "p90": self._percentile(thicknesses, 0.90),
            "plot_html": plot_html,
            "thicknesses": thicknesses,
            "plot_title": plot_title,
        }

    def _create_monte_carlo_figure(self, thicknesses: list[float], title: str):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4.5))
        if thicknesses:
            n = len(thicknesses)
            pct_weight = 100.0 / n
            ax.hist(
                thicknesses,
                bins=60,
                weights=[pct_weight] * n,
                color="#4C78A8",
                edgecolor="white",
            )
        ax.set_title(title)
        ax.set_xlabel("Thickness")
        ax.set_ylabel("Percentage (%)")
        fig.tight_layout()
        return fig

    def _save_monte_carlo_figure_file(
        self,
        thicknesses: list[float],
        title: str,
        fmt: str,
        path: str,
    ) -> None:
        import matplotlib.pyplot as plt

        try:
            fig = self._create_monte_carlo_figure(thicknesses, title)
            save_kw: dict = {"format": fmt}
            if fmt == "png":
                save_kw["dpi"] = 120
            fig.savefig(path, **save_kw)
            plt.close(fig)
            print(f"Saved Monte Carlo histogram to {path}")
        except Exception as exc:
            print(f"Could not save Monte Carlo plot: {exc}")

    def _build_monte_carlo_plot_html(self, thicknesses: list[float], title: str) -> str:
        try:
            import matplotlib.pyplot as plt

            fig = self._create_monte_carlo_figure(thicknesses, title)
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=120)
            plt.close(fig)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            print("Embedded Monte Carlo histogram into output panel.")
            return (
                '<img src="data:image/png;base64,'
                f'{encoded}" style="max-width:100%; height:auto;" />'
            )
        except Exception as exc:
            print(f"Could not render Monte Carlo histogram: {exc}")
            return ""

    def _format_monte_carlo_section(self, stats: dict[str, float | str] | None) -> str:
        if stats is None:
            return ""
        plot_html = str(stats.get("plot_html", ""))
        plot_block = f"{plot_html}<br>" if plot_html else ""
        return (
            "<b>Monte Carlo Distribution</b><br>"
            f"{plot_block}"
            f"N = {int(stats['n'])}<br>"
            f"Mean = {stats['mean']:.6f}<br>"
            f"Std = {stats['std']:.6f}<br>"
            f"P10 = {stats['p10']:.6f}<br>"
            f"P25 = {stats['p25']:.6f}<br>"
            f"P50 = {stats['p50']:.6f}<br>"
            f"P75 = {stats['p75']:.6f}<br>"
            f"P90 = {stats['p90']:.6f}<br><br>"
        )

    def _compute_one_dip(self, tab: ModelTab) -> None:
        inputs = OneDipInputs(
            measured_thickness=tab.value("m"),
            wellbore_inclination_deg=tab.value("delta"),
            formation_dip_deg=tab.value("beta1"),
            wellbore_azimuth_deg=tab.value("phib"),
            dip_azimuth_deg=tab.value("phid1"),
        )
        print("Executing One-dip calculation...")
        result = compute_one_dip(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m", "measured_thickness"),
                ("delta", "wellbore_inclination_deg"),
                ("beta1", "formation_dip_deg"),
                ("phib", "wellbore_azimuth_deg"),
                ("phid1", "dip_azimuth_deg"),
            ],
            wrap_keys={"phib", "phid1"},
            compute_fn=lambda **kwargs: compute_one_dip(OneDipInputs(**kwargs)),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>1</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "T<sub>1</sub> = M(cosδ - sinδ(cos(φ<sub>d1</sub> - φ<sub>b</sub>))"
            "tanβ<sub>1</sub>)cosβ<sub>1</sub><br><br>"
            "<b>Where</b><br>"
            "T<sub>1</sub>: true stratigraphic thickness<br>"
            "M: measured thickness along the well path<br>"
            "δ: wellbore inclination<br>"
            "β<sub>1</sub>: bed dip at entry<br>"
            "φ<sub>b</sub>: wellbore azimuth<br>"
            "φ<sub>d1</sub>: dip azimuth at entry<br>"
            "U<sub>d1</sub>: downward dip-pole unit vector<br>"
            "U<sub>b</sub>: borehole direction unit vector"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m", "M"),
            self._xlsx_input_column(tab, "delta", "delta_deg"),
            self._xlsx_input_column(tab, "beta1", "beta1_deg"),
            self._xlsx_input_column(tab, "phib", "phib_deg"),
            self._xlsx_input_column(tab, "phid1", "phid1_deg"),
        ]
        xlsx_out: list[tuple[str, float | int]] = [
            ("T1", result.true_stratigraphic_thickness),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("One-dip calculation completed.")

    def _compute_average_vector(self, tab: ModelTab) -> None:
        inputs = AverageVectorInputs(
            measured_thickness=tab.value("m2"),
            wellbore_inclination_deg=tab.value("delta2"),
            wellbore_azimuth_deg=tab.value("phib2"),
            formation_dip1_deg=tab.value("beta1_2"),
            dip_azimuth1_deg=tab.value("phid1_2"),
            formation_dip2_deg=tab.value("beta2_2"),
            dip_azimuth2_deg=tab.value("phid2_2"),
        )
        print("Executing Average-vector calculation...")
        result = compute_average_vector(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m2", "measured_thickness"),
                ("delta2", "wellbore_inclination_deg"),
                ("phib2", "wellbore_azimuth_deg"),
                ("beta1_2", "formation_dip1_deg"),
                ("phid1_2", "dip_azimuth1_deg"),
                ("beta2_2", "formation_dip2_deg"),
                ("phid2_2", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib2", "phid1_2", "phid2_2"},
            compute_fn=lambda **kwargs: compute_average_vector(
                AverageVectorInputs(**kwargs)
            ),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>2</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>av</sub> (x,y,z) : "
            f"({result.uav_vector[0]:.6f}, {result.uav_vector[1]:.6f}, "
            f"{result.uav_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "U<sub>av</sub> = (U<sub>d1</sub> + U<sub>d2</sub>) / "
            "||U<sub>d1</sub> + U<sub>d2</sub>||<br>"
            "T<sub>2</sub> = M x (U<sub>av</sub> . U<sub>b</sub>)<br><br>"
            "<b>Where</b><br>"
            "T<sub>2</sub>: true stratigraphic thickness from average-vector model<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>: dip-pole unit vectors at top/base<br>"
            "U<sub>av</sub>: normalized average dip-pole vector<br>"
            "U<sub>b</sub>: borehole unit vector<br>"
            "M: measured thickness along the well path"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m2", "M"),
            self._xlsx_input_column(tab, "delta2", "delta_deg"),
            self._xlsx_input_column(tab, "phib2", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_2", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_2", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_2", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_2", "phid2_deg"),
        ]
        xlsx_out = [("T2", result.true_stratigraphic_thickness)]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Uav", result.uav_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Average-vector calculation completed.")

    def _compute_average_thickness(self, tab: ModelTab) -> None:
        inputs = AverageThicknessInputs(
            measured_thickness=tab.value("m3"),
            wellbore_inclination_deg=tab.value("delta3"),
            wellbore_azimuth_deg=tab.value("phib3"),
            formation_dip1_deg=tab.value("beta1_3"),
            dip_azimuth1_deg=tab.value("phid1_3"),
            formation_dip2_deg=tab.value("beta2_3"),
            dip_azimuth2_deg=tab.value("phid2_3"),
        )
        print("Executing Average-thickness calculation...")
        result = compute_average_thickness(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m3", "measured_thickness"),
                ("delta3", "wellbore_inclination_deg"),
                ("phib3", "wellbore_azimuth_deg"),
                ("beta1_3", "formation_dip1_deg"),
                ("phid1_3", "dip_azimuth1_deg"),
                ("beta2_3", "formation_dip2_deg"),
                ("phid2_3", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib3", "phid1_3", "phid2_3"},
            compute_fn=lambda **kwargs: compute_average_thickness(
                AverageThicknessInputs(**kwargs)
            ),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>3</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br>"
            f"U<sub>d1</sub> . U<sub>b</sub> = {result.ud1_dot_ub:.6f}<br>"
            f"U<sub>d2</sub> . U<sub>b</sub> = {result.ud2_dot_ub:.6f}<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "T<sub>3</sub> = (M x U<sub>d1</sub> . U<sub>b</sub> + "
            "M x U<sub>d2</sub> . U<sub>b</sub>) / 2<br>"
            "T<sub>3</sub> = M x (U<sub>d1</sub> + U<sub>d2</sub>) . "
            "U<sub>b</sub> / 2<br><br>"
            "<b>Where</b><br>"
            "T<sub>3</sub>: true stratigraphic thickness from average-thickness model<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>: dip-pole unit vectors at top/base<br>"
            "U<sub>b</sub>: borehole unit vector<br>"
            "M: measured thickness along the well path<br>"
            ". : dot product"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m3", "M"),
            self._xlsx_input_column(tab, "delta3", "delta_deg"),
            self._xlsx_input_column(tab, "phib3", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_3", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_3", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_3", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_3", "phid2_deg"),
        ]
        xlsx_out = [("T3", result.true_stratigraphic_thickness)]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        xlsx_out.append(("Ud1_dot_Ub", result.ud1_dot_ub))
        xlsx_out.append(("Ud2_dot_Ub", result.ud2_dot_ub))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Average-thickness calculation completed.")

    def _compute_mixed_average(self, tab: ModelTab) -> None:
        inputs = MixedAverageInputs(
            measured_thickness=tab.value("m4"),
            wellbore_inclination_deg=tab.value("delta4"),
            wellbore_azimuth_deg=tab.value("phib4"),
            formation_dip1_deg=tab.value("beta1_4"),
            dip_azimuth1_deg=tab.value("phid1_4"),
            formation_dip2_deg=tab.value("beta2_4"),
            dip_azimuth2_deg=tab.value("phid2_4"),
        )
        print("Executing Mixed Average calculation...")
        result = compute_mixed_average(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m4", "measured_thickness"),
                ("delta4", "wellbore_inclination_deg"),
                ("phib4", "wellbore_azimuth_deg"),
                ("beta1_4", "formation_dip1_deg"),
                ("phid1_4", "dip_azimuth1_deg"),
                ("beta2_4", "formation_dip2_deg"),
                ("phid2_4", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib4", "phid1_4", "phid2_4"},
            compute_fn=lambda **kwargs: compute_mixed_average(
                MixedAverageInputs(**kwargs)
            ),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>4</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            f"T<sub>2</sub> = {result.t2_value:.6f}<br>"
            f"T<sub>3</sub> = {result.t3_value:.6f}<br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>av</sub> (x,y,z) : "
            f"({result.uav_vector[0]:.6f}, {result.uav_vector[1]:.6f}, "
            f"{result.uav_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "T<sub>4</sub> = (T<sub>2</sub> + T<sub>3</sub>) / 2<br><br>"
            "<b>Where</b><br>"
            "T<sub>4</sub>: mixed-average thickness (mean of T<sub>2</sub> and T<sub>3</sub>)<br>"
            "T<sub>2</sub>: average-vector thickness<br>"
            "T<sub>3</sub>: average-thickness value<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>, U<sub>av</sub>, U<sub>b</sub>: "
            "supporting vectors from component models"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m4", "M"),
            self._xlsx_input_column(tab, "delta4", "delta_deg"),
            self._xlsx_input_column(tab, "phib4", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_4", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_4", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_4", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_4", "phid2_deg"),
        ]
        xlsx_out = [
            ("T4", result.true_stratigraphic_thickness),
            ("T2_component", result.t2_value),
            ("T3_component", result.t3_value),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Uav", result.uav_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Mixed Average calculation completed.")

    def _compute_concentric_fold(self, tab: ModelTab) -> None:
        inputs = ConcentricFoldInputs(
            measured_thickness=tab.value("m5"),
            wellbore_inclination_deg=tab.value("delta5"),
            wellbore_azimuth_deg=tab.value("phib5"),
            formation_dip1_deg=tab.value("beta1_5"),
            dip_azimuth1_deg=tab.value("phid1_5"),
            formation_dip2_deg=tab.value("beta2_5"),
            dip_azimuth2_deg=tab.value("phid2_5"),
        )
        print("Executing Concentric Fold calculation...")
        result = compute_concentric_fold(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m5", "measured_thickness"),
                ("delta5", "wellbore_inclination_deg"),
                ("phib5", "wellbore_azimuth_deg"),
                ("beta1_5", "formation_dip1_deg"),
                ("phid1_5", "dip_azimuth1_deg"),
                ("beta2_5", "formation_dip2_deg"),
                ("phid2_5", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib5", "phid1_5", "phid2_5"},
            compute_fn=lambda **kwargs: compute_concentric_fold(
                ConcentricFoldInputs(**kwargs)
            ),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>5</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            f"β'<sub>2</sub> = {result.beta2_prime_deg:.6f} deg<br>"
            f"M' = {result.m_prime:.6f}<br>"
            f"γ = {result.gamma_deg:.6f} deg<br>"
            f"α = {result.alpha_deg:.6f} deg<br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U'<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_prime_vector[0]:.6f}, {result.ud2_prime_vector[1]:.6f}, "
            f"{result.ud2_prime_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br>"
            "N<sub>dc</sub> (x,y,z) : "
            f"({result.ndc_vector[0]:.6f}, {result.ndc_vector[1]:.6f}, "
            f"{result.ndc_vector[2]:.6f})<br>"
            "U<sub>c</sub> (x,y,z) : "
            f"({result.c_vector[0]:.6f}, {result.c_vector[1]:.6f}, "
            f"{result.c_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "β'<sub>2</sub> = arctan(tanβ<sub>2</sub>cos(φ<sub>d1</sub>-φ<sub>d2</sub>))<br>"
            "U<sub>d1</sub> = (-cos φ<sub>d1</sub> sin β<sub>1</sub>, "
            "-sin φ<sub>d1</sub> sin β<sub>1</sub>, cos β<sub>1</sub>)<br>"
            "U'<sub>d2</sub> = (-cos φ<sub>d1</sub> sin β'<sub>2</sub>, "
            "-sin φ<sub>d1</sub> sin β'<sub>2</sub>, cos β'<sub>2</sub>)<br>"
            "N<sub>dc</sub> = (U<sub>d1</sub> x U'<sub>d2</sub>) / "
            "||U<sub>d1</sub> x U'<sub>d2</sub>||<br>"
            "M' = ||M<sub>b</sub> - N<sub>dc</sub>(N<sub>dc</sub> . M<sub>b</sub>)||; "
            "M<sub>b</sub> = M U<sub>b</sub><br>"
            "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>|| with M'<sub>b</sub> = "
            "M<sub>b</sub> - N<sub>dc</sub>(N<sub>dc</sub> . M<sub>b</sub>)<br>"
            "U<sub>c</sub> = (U<sub>d1</sub> - U'<sub>d2</sub>) / "
            "||U<sub>d1</sub> - U'<sub>d2</sub>||<br>"
            "γ = arccos(U<sub>c</sub> . U'<sub>b</sub>)<br>"
            "α = arccos(U<sub>d1</sub> . U'<sub>b</sub>)<br>"
            "T<sub>5</sub> = M' (sinγ / sinα)<br><br>"
            "<b>Where</b><br>"
            "T<sub>5</sub>: concentric-fold thickness (Xu et al.; M' after Berg, 2011)<br>"
            "β'<sub>2</sub>: azimuth-corrected base dip<br>"
            "U<sub>d1</sub>, U'<sub>d2</sub>: top and corrected-base dip vectors (fixed bed azimuth φ<sub>d1</sub>)<br>"
            "N<sub>dc</sub>: normal to dip-vector plane<br>"
            "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>"
            "U<sub>c</sub>: normalized difference of dip poles; U'<sub>b</sub>: unit projection of M<sub>b</sub><br>"
            "γ: angle between U<sub>c</sub> and U'<sub>b</sub>; "
            "α: angle between U<sub>d1</sub> and U'<sub>b</sub>"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m5", "M"),
            self._xlsx_input_column(tab, "delta5", "delta_deg"),
            self._xlsx_input_column(tab, "phib5", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_5", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_5", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_5", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_5", "phid2_deg"),
        ]
        xlsx_out = [
            ("T5", result.true_stratigraphic_thickness),
            ("beta2_prime_deg", result.beta2_prime_deg),
            ("M_prime", result.m_prime),
            ("gamma_deg", result.gamma_deg),
            ("alpha_deg", result.alpha_deg),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2_prime", result.ud2_prime_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ndc", result.ndc_vector))
        xlsx_out.extend(self._vec3_csv_rows("Uc", result.c_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Concentric Fold calculation completed.")

    def _compute_plunging_concentric_fold(self, tab: ModelTab) -> None:
        inputs = PlungingConcentricFoldInputs(
            measured_thickness=tab.value("m6"),
            wellbore_inclination_deg=tab.value("delta6"),
            wellbore_azimuth_deg=tab.value("phib6"),
            formation_dip1_deg=tab.value("beta1_6"),
            dip_azimuth1_deg=tab.value("phid1_6"),
            formation_dip2_deg=tab.value("beta2_6"),
            dip_azimuth2_deg=tab.value("phid2_6"),
        )
        print("Executing Plunging Concentric Fold calculation...")
        result = compute_plunging_concentric_fold(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m6", "measured_thickness"),
                ("delta6", "wellbore_inclination_deg"),
                ("phib6", "wellbore_azimuth_deg"),
                ("beta1_6", "formation_dip1_deg"),
                ("phid1_6", "dip_azimuth1_deg"),
                ("beta2_6", "formation_dip2_deg"),
                ("phid2_6", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib6", "phid1_6", "phid2_6"},
            compute_fn=lambda **kwargs: compute_plunging_concentric_fold(
                PlungingConcentricFoldInputs(**kwargs)
            ),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        output = (
            "<b>Result</b><br>"
            f"T<sub>6</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            f"M' = {result.m_prime:.6f}<br>"
            f"γ = {result.gamma_deg:.6f} deg<br>"
            f"α = {result.alpha_deg:.6f} deg<br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br>"
            "N<sub>dp</sub> (x,y,z) : "
            f"({result.ndp_vector[0]:.6f}, {result.ndp_vector[1]:.6f}, "
            f"{result.ndp_vector[2]:.6f})<br>"
            "U<sub>c</sub> (x,y,z) : "
            f"({result.c_vector[0]:.6f}, {result.c_vector[1]:.6f}, "
            f"{result.c_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "N<sub>dp</sub> = (U<sub>d1</sub> x U<sub>d2</sub>) / "
            "||U<sub>d1</sub> x U<sub>d2</sub>||<br>"
            "M' = ||M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)||; "
            "M<sub>b</sub> = M U<sub>b</sub><br>"
            "M'<sub>b</sub> = M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>); "
            "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>||<br>"
            "U<sub>c</sub> = (U<sub>d1</sub> - U<sub>d2</sub>) / "
            "||U<sub>d1</sub> - U<sub>d2</sub>||<br>"
            "γ = arccos(U<sub>c</sub> . U'<sub>b</sub>)<br>"
            "α = arccos(U<sub>d1</sub> . U<sub>c</sub>)<br>"
            "T<sub>6</sub> = M' (sinγ / sinα)<br><br>"
            "<b>Where</b><br>"
            "T<sub>6</sub>: plunging-fold thickness (no base azimuth correction)<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>: top and base dip-pole vectors<br>"
            "N<sub>dp</sub>: normal to the plane of U<sub>d1</sub> and U<sub>d2</sub><br>"
            "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>"
            "U<sub>c</sub>: normalized (U<sub>d1</sub> - U<sub>d2</sub>)<br>"
            "γ: angle between U<sub>c</sub> and U'<sub>b</sub>; "
            "α: angle between U<sub>d1</sub> and U<sub>c</sub>"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m6", "M"),
            self._xlsx_input_column(tab, "delta6", "delta_deg"),
            self._xlsx_input_column(tab, "phib6", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_6", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_6", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_6", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_6", "phid2_deg"),
        ]
        xlsx_out = [
            ("T6", result.true_stratigraphic_thickness),
            ("M_prime", result.m_prime),
            ("gamma_deg", result.gamma_deg),
            ("alpha_deg", result.alpha_deg),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ndp", result.ndp_vector))
        xlsx_out.extend(self._vec3_csv_rows("Uc", result.c_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Plunging Concentric Fold calculation completed.")

    def _compute_top_normal(self, tab: ModelTab) -> None:
        inputs = TopNormalInputs(
            measured_thickness=tab.value("m7"),
            wellbore_inclination_deg=tab.value("delta7"),
            wellbore_azimuth_deg=tab.value("phib7"),
            formation_dip1_deg=tab.value("beta1_7"),
            dip_azimuth1_deg=tab.value("phid1_7"),
            formation_dip2_deg=tab.value("beta2_7"),
            dip_azimuth2_deg=tab.value("phid2_7"),
        )
        print("Executing Top-normal calculation...")
        result = compute_top_normal(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m7", "measured_thickness"),
                ("delta7", "wellbore_inclination_deg"),
                ("phib7", "wellbore_azimuth_deg"),
                ("beta1_7", "formation_dip1_deg"),
                ("phid1_7", "dip_azimuth1_deg"),
                ("beta2_7", "formation_dip2_deg"),
                ("phid2_7", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib7", "phid1_7", "phid2_7"},
            compute_fn=lambda **kwargs: compute_top_normal(TopNormalInputs(**kwargs)),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        branch_note = (
            "Top-normal = M' cos(α+η)/cos(η) &nbsp; (S ≥ 0)"
            if result.uses_positive_s_branch
            else "Top-normal = M' cos(α−η)/cos(η) &nbsp; (S &lt; 0)"
        )
        output = (
            "<b>Result</b><br>"
            "Top-normal (stratigraphic thickness, normal to top bed): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            f"M' = {result.m_prime:.6f}<br>"
            f"α = {result.alpha_deg:.6f} deg<br>"
            f"η = {result.eta_deg:.6f} deg<br>"
            f"S = N<sub>dp</sub> . U'<sub>b</sub> = {result.s_value:.6f}<br>"
            f"Branch: {branch_note}<br><br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br>"
            "N<sub>dp</sub> (x,y,z) : "
            f"({result.ndp_vector[0]:.6f}, {result.ndp_vector[1]:.6f}, "
            f"{result.ndp_vector[2]:.6f})<br>"
            "U'<sub>b</sub> (x,y,z) : "
            f"({result.ub_prime_vector[0]:.6f}, {result.ub_prime_vector[1]:.6f}, "
            f"{result.ub_prime_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "N<sub>dp</sub> = (U<sub>d1</sub> x U<sub>d2</sub>) / "
            "||U<sub>d1</sub> x U<sub>d2</sub>||<br>"
            "M' = ||M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)||; "
            "M<sub>b</sub> = M U<sub>b</sub><br>"
            "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>|| with M'<sub>b</sub> = "
            "M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)<br>"
            "α = arccos(U<sub>d1</sub> . U'<sub>b</sub>)<br>"
            "η = arccos(U<sub>d1</sub> . U<sub>d2</sub>)<br>"
            "S = N<sub>dp</sub> . U'<sub>b</sub><br>"
            "If S &lt; 0: Top-normal = M' cos(α − η) / cos(η) &nbsp; (eq. 31; paper T<sub>7</sub>)<br>"
            "If S ≥ 0: Top-normal = M' cos(α + η) / cos(η) &nbsp; (eq. 35; paper T<sub>7</sub>)<br>"
            "Also Top-normal = M' (sinγ / sinμ) = M' cos(α ∓ η) / cos(η) (Berg, 2011)<br><br>"
            "<b>Where</b><br>"
            "Top-normal: thickness for M measured normal to the top bed (paper T<sub>7</sub>)<br>"
            "η: angle between dip poles at top and base; S selects thickening sense<br>"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m7", "M"),
            self._xlsx_input_column(tab, "delta7", "delta_deg"),
            self._xlsx_input_column(tab, "phib7", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_7", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_7", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_7", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_7", "phid2_deg"),
        ]
        xlsx_out = [
            ("Top_normal_T7", result.true_stratigraphic_thickness),
            ("M_prime", result.m_prime),
            ("alpha_deg", result.alpha_deg),
            ("eta_deg", result.eta_deg),
            ("S_Ndp_dot_Ub_prime", result.s_value),
            (
                "Top_normal_positive_S_branch",
                1.0 if result.uses_positive_s_branch else 0.0,
            ),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ndp", result.ndp_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub_prime", result.ub_prime_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Top-normal calculation completed.")

    def _compute_equal_angle(self, tab: ModelTab) -> None:
        inputs = EqualAngleInputs(
            measured_thickness=tab.value("m8"),
            wellbore_inclination_deg=tab.value("delta8"),
            wellbore_azimuth_deg=tab.value("phib8"),
            formation_dip1_deg=tab.value("beta1_8"),
            dip_azimuth1_deg=tab.value("phid1_8"),
            formation_dip2_deg=tab.value("beta2_8"),
            dip_azimuth2_deg=tab.value("phid2_8"),
        )
        print("Executing Equal-angle (T8) calculation...")
        result = compute_equal_angle(inputs)
        mc_stats = self._run_monte_carlo(
            tab=tab,
            key_to_field=[
                ("m8", "measured_thickness"),
                ("delta8", "wellbore_inclination_deg"),
                ("phib8", "wellbore_azimuth_deg"),
                ("beta1_8", "formation_dip1_deg"),
                ("phid1_8", "dip_azimuth1_deg"),
                ("beta2_8", "formation_dip2_deg"),
                ("phid2_8", "dip_azimuth2_deg"),
            ],
            wrap_keys={"phib8", "phid1_8", "phid2_8"},
            compute_fn=lambda **kwargs: compute_equal_angle(EqualAngleInputs(**kwargs)),
        )
        mc_section = self._format_monte_carlo_section(mc_stats)
        branch_note = (
            "Top-normal = M' cos(α+η)/cos(η) &nbsp; (S ≥ 0)"
            if result.uses_positive_s_branch
            else "Top-normal = M' cos(α−η)/cos(η) &nbsp; (S &lt; 0)"
        )
        output = (
            "<b>Result</b><br>"
            f"T<sub>8</sub> (equal-angle): {result.true_stratigraphic_thickness:.6f}<br>"
            f"Top-normal (intermediate): {result.top_normal_thickness:.6f}<br><br>"
            "<b>Quantities</b><br>"
            f"M' = {result.m_prime:.6f}<br>"
            f"α = {result.alpha_deg:.6f} deg<br>"
            f"η = {result.eta_deg:.6f} deg<br>"
            f"S = N<sub>dp</sub> . U'<sub>b</sub> = {result.s_value:.6f}<br>"
            f"Branch: {branch_note}<br><br>"
            "U<sub>d1</sub> (x,y,z) : "
            f"({result.ud1_vector[0]:.6f}, {result.ud1_vector[1]:.6f}, "
            f"{result.ud1_vector[2]:.6f})<br>"
            "U<sub>d2</sub> (x,y,z) : "
            f"({result.ud2_vector[0]:.6f}, {result.ud2_vector[1]:.6f}, "
            f"{result.ud2_vector[2]:.6f})<br>"
            "U<sub>b</sub> (x,y,z) : "
            f"({result.ub_vector[0]:.6f}, {result.ub_vector[1]:.6f}, "
            f"{result.ub_vector[2]:.6f})<br>"
            "N<sub>dp</sub> (x,y,z) : "
            f"({result.ndp_vector[0]:.6f}, {result.ndp_vector[1]:.6f}, "
            f"{result.ndp_vector[2]:.6f})<br>"
            "U'<sub>b</sub> (x,y,z) : "
            f"({result.ub_prime_vector[0]:.6f}, {result.ub_prime_vector[1]:.6f}, "
            f"{result.ub_prime_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "Same intermediate quantities as Top-normal (N<sub>dp</sub>, M', U'<sub>b</sub>, α, η, S)<br>"
            "Top-normal = M' cos(α ∓ η) / cos(η) per S (paper T<sub>7</sub>)<br>"
            "T<sub>8</sub> = Top-normal × cos(η / 2) &nbsp; (eq. 38; equal-angle method)<br><br>"
            "<b>Where</b><br>"
            "T<sub>8</sub>: equal-angle thickness; η = arccos(U<sub>d1</sub> · U<sub>d2</sub>) (eq. 33)<br>"
        )
        xlsx_in = [
            self._xlsx_input_column(tab, "m8", "M"),
            self._xlsx_input_column(tab, "delta8", "delta_deg"),
            self._xlsx_input_column(tab, "phib8", "phib_deg"),
            self._xlsx_input_column(tab, "beta1_8", "beta1_deg"),
            self._xlsx_input_column(tab, "phid1_8", "phid1_deg"),
            self._xlsx_input_column(tab, "beta2_8", "beta2_deg"),
            self._xlsx_input_column(tab, "phid2_8", "phid2_deg"),
        ]
        xlsx_out = [
            ("T8_equal_angle", result.true_stratigraphic_thickness),
            ("Top_normal_intermediate", result.top_normal_thickness),
            ("M_prime", result.m_prime),
            ("alpha_deg", result.alpha_deg),
            ("eta_deg", result.eta_deg),
            ("S_Ndp_dot_Ub_prime", result.s_value),
            (
                "Top_normal_positive_S_branch",
                1.0 if result.uses_positive_s_branch else 0.0,
            ),
        ]
        xlsx_out.extend(self._vec3_csv_rows("Ud1", result.ud1_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ud2", result.ud2_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub", result.ub_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ndp", result.ndp_vector))
        xlsx_out.extend(self._vec3_csv_rows("Ub_prime", result.ub_prime_vector))
        self._apply_model_output(
            tab,
            output,
            mc_stats,
            xlsx_in,
            xlsx_out,
            self._mc_excel_rows_from_stats(mc_stats),
        )
        print("Equal-angle (T8) calculation completed.")
