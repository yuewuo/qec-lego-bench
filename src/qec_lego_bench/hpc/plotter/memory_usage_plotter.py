from ..monte_carlo import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from IPython import display
from dataclasses import field
import psutil
from .logical_error_rate_plotter import closed_figure


@dataclass
class MemoryUsagePlotter:

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)
    start: float = field(default_factory=lambda: time.time())
    time_vec: list[float] = field(default_factory=list)
    rss_vec: list[float] = field(default_factory=list)
    update_interval_sec: float = 1

    def __call__(self, executor: MonteCarloJobExecutor):
        last_time = 0.0
        if self.time_vec:
            last_time = self.time_vec[-1]
        if time.time() - self.start < last_time + self.update_interval_sec:
            # skip because we do not want to blow the memory by recording so many data points
            return
        process = psutil.Process()
        self.time_vec.append(time.time() - self.start)
        self.rss_vec.append(process.memory_info().rss / 1e6)
        # plot
        fig = self.fig
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("time (s)")
        ax.set_ylabel("memory usage (MB)")
        ax.errorbar(self.time_vec, self.rss_vec)
        ax.set_title("Memory Usage")
        self.hdisplay.update(fig)
