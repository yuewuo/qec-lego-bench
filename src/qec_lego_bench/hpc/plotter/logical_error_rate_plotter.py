from ..monte_carlo import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from IPython import display
from dataclasses import field
from typing import Optional


@dataclass
class LogicalErrorRatePlotter:
    d_vec: list[int]
    p_vec: list[float]
    xlim: Optional[tuple[float, float]] = None
    ylim: Optional[tuple[float, float]] = None

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=lambda: plt.figure())

    def __post_init__(self):
        self.fig.clear()

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("physical error rate $p$")
        ax.set_ylabel("logical error rate $p_L$")
        if self.xlim is not None:
            ax.set_xlim(*self.xlim)
        else:
            ax.set_xlim(min(self.p_vec) / 2, max(self.p_vec) * 2)
        ax.set_xscale("log")
        if self.ylim is not None:
            ax.set_ylim(*self.ylim)
        else:
            ax.set_ylim(1e-4, 1)
        ax.set_yscale("log")
        for d in self.d_vec:
            x_vec = []
            y_vec = []
            err_vec = []
            for p in self.p_vec:
                job = executor.get_job(d=d, p=p)
                if job is None or job.result is None:
                    continue
                x_vec.append(p)
                stats = job.result.stats_of(job)  # type: ignore
                y_vec.append(stats.failure_rate_value)
                err_vec.append(stats.failure_rate_uncertainty)
            ax.errorbar(x_vec, y_vec, err_vec, label=f"d={d}")
        fig.legend()
        self.hdisplay.update(fig)
