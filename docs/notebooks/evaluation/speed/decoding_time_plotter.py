from dataclasses import dataclass, field
from IPython import display
from matplotlib.figure import Figure
from qec_lego_bench.hpc.job_store import Job
from qec_lego_bench.hpc.plotter.logical_error_rate_plotter import *


@dataclass
class DecodingTimePlotter:
    rounds: int
    p_vec: list[float]
    d_vec: list[int]
    max_per_round_time: float

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, executor: MonteCarloJobExecutor):
        # add more d if the previous one is not too slow
        for p in self.p_vec:
            for d_idx, d in enumerate(self.d_vec[:-1]):
                job = executor.get_job(d=d, p=p, rounds=self.rounds)
                if job is None or job.result is None:
                    continue
                per_round_time = job.result.decoding_time / self.rounds
                if per_round_time > self.max_per_round_time:
                    break
                next_d = self.d_vec[d_idx + 1]
                next_job = executor.get_job(d=next_d, p=p, rounds=self.rounds)
                if next_job is None:
                    executor.add_job(Job(d=next_d, p=p, rounds=self.rounds))

        # plot the results
        fig = self.fig
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("code distance $d$")
        ax.set_ylabel("decoding time per measurement round")
        ax.set_xlim(min(self.d_vec) / 1.2, max(self.d_vec) * 1.2)
        ax.set_xscale("log")
        ax.set_ylim(1e-10, 1e3)
        ax.set_yscale("log")
        for p in self.p_vec:
            x_vec = []
            y_vec = []
            for d in self.d_vec:
                job = executor.get_job(d=d, p=p, rounds=self.rounds)
                if job is None or job.result is None:
                    continue
                x_vec.append(d)
                y_vec.append(job.result.decoding_time / self.rounds)
            ax.errorbar(x_vec, y_vec, label=f"p={p}", fmt="o-")
        ax.legend()
        self.hdisplay.update(fig)
