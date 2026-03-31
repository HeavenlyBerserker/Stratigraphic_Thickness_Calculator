from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

from source.models import OneDipInputs, compute_one_dip
from source.widgets import ModelTab


def _coming_soon_calculation(tab: ModelTab, model_name: str) -> None:
    print(f"{model_name}: calculation requested.")
    tab.set_output(
        "This model is scaffolded and ready for implementation.\n"
        "Add model-specific equations and validation in source/app.py."
    )


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

        self.tabs.addTab(
            ModelTab(
                "Two-dip Model",
                lambda tab: _coming_soon_calculation(tab, "Two-dip"),
            ),
            "Two-dip",
        )
        self.tabs.addTab(
            ModelTab(
                "Average-thickness Model",
                lambda tab: _coming_soon_calculation(tab, "Average-thickness"),
            ),
            "Average-thickness",
        )
        self.tabs.addTab(
            ModelTab(
                "Mixed Average Model",
                lambda tab: _coming_soon_calculation(tab, "Mixed Average"),
            ),
            "Mixed Average",
        )
        self.tabs.addTab(
            ModelTab(
                "Concentric Fold Model",
                lambda tab: _coming_soon_calculation(tab, "Concentric Fold"),
            ),
            "Concentric Fold",
        )
        self.tabs.addTab(
            ModelTab(
                "Plunging Concentric Fold Model",
                lambda tab: _coming_soon_calculation(
                    tab, "Plunging Concentric Fold"
                ),
            ),
            "Plunging Concentric Fold",
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
        output = (
            "<b>Formula:</b><br>"
            "T<sub>1</sub> = M(cosδ - sinδ(cos(φ<sub>d1</sub> - φ<sub>b</sub>))"
            "tanβ<sub>1</sub>)cosβ<sub>1</sub><br><br>"
            f"T<sub>1</sub> (True Stratigraphic Thickness): "
            f"{result.true_stratigraphic_thickness:.6f}<br><br>"
            f"U<sub>d1</sub> (Downward dip-pole unit vector):<br>"
            f"&nbsp;&nbsp;x={result.ud1_vector[0]:.6f}, "
            f"y={result.ud1_vector[1]:.6f}, "
            f"z={result.ud1_vector[2]:.6f}<br><br>"
            f"U<sub>b</sub> (Borehole unit vector):<br>"
            f"&nbsp;&nbsp;x={result.ub_vector[0]:.6f}, "
            f"y={result.ub_vector[1]:.6f}, "
            f"z={result.ub_vector[2]:.6f}"
        )
        tab.set_output(output, is_html=True)
        print("One-dip calculation completed.")
