from __future__ import annotations

import base64
import io
import random
import sys
from statistics import mean, pstdev
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

from source.models import (
    AverageThicknessInputs,
    AverageVectorInputs,
    ConcentricFoldInputs,
    MixedAverageInputs,
    OneDipInputs,
    PlungingConcentricFoldInputs,
    compute_average_thickness,
    compute_average_vector,
    compute_concentric_fold,
    compute_mixed_average,
    compute_one_dip,
    compute_plunging_concentric_fold,
)
from source.widgets import ModelTab


class StratigraphicCalculatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Stratigraphic Thickness Calculator")
        self.resize(1200, 800)
        self._set_window_logo()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_tabs()

    def _set_window_logo(self) -> None:
        if getattr(sys, "frozen", False):
            base_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        else:
            base_dir = Path(__file__).resolve().parent.parent
        icon_path = base_dir / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _build_tabs(self) -> None:
        one_dip_tab = ModelTab("One-dip Model", self._compute_one_dip)
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
        self.tabs.addTab(one_dip_tab, "One-dip")

        average_vector_tab = ModelTab(
            "Average-vector Model",
            self._compute_average_vector,
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
        self.tabs.addTab(average_vector_tab, "Average-vector")
        average_thickness_tab = ModelTab(
            "Average-thickness Model",
            self._compute_average_thickness,
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
        self.tabs.addTab(average_thickness_tab, "Average-thickness")
        mixed_average_tab = ModelTab(
            "Mixed Average Model",
            self._compute_mixed_average,
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
        self.tabs.addTab(mixed_average_tab, "Mixed Average")
        concentric_fold_tab = ModelTab(
            "Concentric Fold Model",
            self._compute_concentric_fold,
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
        self.tabs.addTab(concentric_fold_tab, "Concentric Fold")
        plunging_fold_tab = ModelTab(
            "Plunging Concentric Fold Model",
            self._compute_plunging_concentric_fold,
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
        self.tabs.addTab(plunging_fold_tab, "Plunging Concentric Fold")

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
        return any(tab.std(key) > 0.0 for key in keys)

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

        plot_html = self._build_monte_carlo_plot_html(
            thicknesses,
            f"{self.tabs.tabText(self.tabs.currentIndex())} Monte Carlo Thickness Distribution",
        )
        return {
            "n": float(len(thicknesses)),
            "mean": mean(thicknesses),
            "std": pstdev(thicknesses),
            "p10": self._percentile(thicknesses, 0.10),
            "p50": self._percentile(thicknesses, 0.50),
            "p90": self._percentile(thicknesses, 0.90),
            "plot_html": plot_html,
        }

    def _build_monte_carlo_plot_html(self, thicknesses: list[float], title: str) -> str:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.hist(thicknesses, bins=60, color="#4C78A8", edgecolor="white")
            ax.set_title(title)
            ax.set_xlabel("Thickness")
            ax.set_ylabel("Frequency")
            fig.tight_layout()
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
            f"P50 = {stats['p50']:.6f}<br>"
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
        tab.set_output(output, is_html=True)
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
        tab.set_output(output, is_html=True)
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
        tab.set_output(output, is_html=True)
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
            "T<sub>4</sub> = T<sub>2</sub> + T<sub>3</sub><br><br>"
            "<b>Where</b><br>"
            "T<sub>4</sub>: mixed-average thickness<br>"
            "T<sub>2</sub>: average-vector thickness<br>"
            "T<sub>3</sub>: average-thickness value<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>, U<sub>av</sub>, U<sub>b</sub>: "
            "supporting vectors from component models"
        )
        tab.set_output(output, is_html=True)
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
            "C (x,y,z) : "
            f"({result.c_vector[0]:.6f}, {result.c_vector[1]:.6f}, "
            f"{result.c_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "β'<sub>2</sub> = arctan(tanβ<sub>2</sub>cos(φ<sub>d1</sub>-φ<sub>d2</sub>))<br>"
            "N<sub>dc</sub> = (U<sub>d1</sub> x U'<sub>d2</sub>) / "
            "||U<sub>d1</sub> x U'<sub>d2</sub>||<br>"
            "M' = ||M<sub>b</sub> - N<sub>dc</sub>(N<sub>dc</sub> . M<sub>b</sub>)||<br>"
            "C = (U<sub>d1</sub> - U'<sub>d2</sub>) / ||U<sub>d1</sub> - U'<sub>d2</sub>||<br>"
            "γ = arccos(C . M'<sub>b,unit</sub>)<br>"
            "α = arccos(U<sub>d1</sub> . U'<sub>d2</sub>)<br>"
            "T<sub>5</sub> = M' (sinγ / sinα)<br><br>"
            "<b>Where</b><br>"
            "T<sub>5</sub>: concentric-fold thickness<br>"
            "β'<sub>2</sub>: azimuth-corrected base dip<br>"
            "U<sub>d1</sub>, U'<sub>d2</sub>: top and corrected-base dip vectors<br>"
            "N<sub>dc</sub>: normal to dip-vector plane<br>"
            "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>"
            "C: normalized difference vector; γ and α are geometry angles"
        )
        tab.set_output(output, is_html=True)
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
            f"T<sub>5</sub> (True Stratigraphic Thickness): "
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
            "C (x,y,z) : "
            f"({result.c_vector[0]:.6f}, {result.c_vector[1]:.6f}, "
            f"{result.c_vector[2]:.6f})<br><br>"
            f"{mc_section}"
            "<b>Formula</b><br>"
            "N<sub>dp</sub> = (U<sub>d1</sub> x U<sub>d2</sub>) / "
            "||U<sub>d1</sub> x U<sub>d2</sub>||<br>"
            "M' = ||M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)||<br>"
            "M'<sub>b</sub> = M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)<br>"
            "C = (U<sub>d1</sub> - U<sub>d2</sub>) / "
            "||U<sub>d1</sub> - U<sub>d2</sub>||<br>"
            "γ = arccos(C . M'<sub>b,unit</sub>)<br>"
            "α = arccos(U<sub>d1</sub> . U<sub>d2</sub>)<br>"
            "T<sub>5</sub> = M' (sinγ / sinα)<br><br>"
            "<b>Where</b><br>"
            "T<sub>5</sub>: plunging concentric-fold thickness<br>"
            "U<sub>d1</sub>, U<sub>d2</sub>: top and base dip vectors<br>"
            "N<sub>dp</sub>: normal to dip-vector plane<br>"
            "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>"
            "C: normalized difference vector; γ and α are geometry angles"
        )
        tab.set_output(output, is_html=True)
        print("Plunging Concentric Fold calculation completed.")
