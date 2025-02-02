from ..monte_carlo import *
from matplotlib.figure import Figure
from IPython import display
from typing import Any
from dataclasses import field
from .logical_error_rate_plotter import closed_figure
from ..submitter.adaptive_p_vec_submitter import AdaptivePVec


@dataclass
class AdaptivePVecPlotter:
    config_vec: list[dict[str, Any]]
    ap_vec: AdaptivePVec

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        fig.set_size_inches(10, 12)
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("physical error rate $p$")
        ax.set_ylabel("logical error rate $p_L$")
        ax.set_xlim(1e-5, 1)
        ax.set_xscale("log")
        ax.set_ylim(1e-6, 1)
        ax.set_yscale("log")
        for config in self.config_vec:
            x_vec = []
            y_vec = []
            err_vec = []
            jobs = self.ap_vec.jobs(executor, config)
            for job in jobs:
                p: float = job["p"]
                if job is None or job.result is None:
                    continue
                x_vec.append(p)
                stats = job.result.stats_of(job)  # type: ignore
                y_vec.append(stats.failure_rate_value)
                err_vec.append(stats.failure_rate_uncertainty)
            label = ",".join([f"{key}={value}" for key, value in config.items()])
            ax.errorbar(x_vec, y_vec, err_vec, label=label)
        ax.legend()
        self.hdisplay.update(fig)
