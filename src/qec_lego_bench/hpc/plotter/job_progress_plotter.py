from ..monte_carlo import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from IPython import display
from typing import cast
from dataclasses import field


@dataclass
class JobProgressPlotter:
    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=lambda: plt.figure())

    def __post_init__(self):
        self.fig.clear()

    def __call__(
        self, executor: MonteCarloJobExecutor, show_logical_error: bool = True
    ):
        fig = self.fig
        ax = fig.gca()
        ax.clear()
        pending_jobs = []
        finished_jobs = []
        column_headers = [
            "Job",
            "Finished",
            "Pending",
            "Submitted",
            f"{len(executor.pending_futures)} jobs",
            "Total",
            "Duration",
        ]
        if show_logical_error:
            column_headers.extend(["Errors", "Discards", "Error Rate"])
        job_pending_futures_count = {job: 0 for job in executor}
        for future in executor.pending_futures:
            job = executor.future_info[future]
            job_pending_futures_count[job] += 1
        for job in executor:
            if job.expecting_shots == 0:
                continue
            submitted = job.pending_shots
            pending_submit = executor.pending_submit.get(job)
            if pending_submit is not None:
                submitted -= pending_submit[0]
            job_future_percentage = 0
            if len(executor.pending_futures) > 0:
                job_future_percentage = job_pending_futures_count[job] / len(
                    executor.pending_futures
                )
            row = [
                job,
                repr(job),
                f"{job.finished_shots} ({int(job.finished_shots/job.expecting_shots*100)}%)",
                f"{job.pending_shots} ({int(job.pending_shots/job.expecting_shots*100)}%)",
                f"{submitted} ({int(submitted/job.expecting_shots*100)}%)",
                f"{job_pending_futures_count[job]} ({int(job_future_percentage*100)}%)",
                job.expecting_shots,
                f"{job.duration:.1f}s ({job.duration/60:.1f}min)",
            ]
            if show_logical_error:
                if job.result is not None:
                    stats = job.result.stats_of(job)  # type: ignore
                    row.extend(
                        [
                            stats.errors,
                            stats.discards,
                            f"{stats.failure_rate:.1uS}",
                        ]
                    )
                else:
                    row.extend(["-", "-", "-"])
            if job.pending_shots > 0:
                pending_jobs.append(row)
            else:
                finished_jobs.append(row)
        pending_jobs.sort(key=lambda row: -cast(MonteCarloJob, row[0]).duration)
        finished_jobs.sort(key=lambda row: -cast(MonteCarloJob, row[0]).duration)
        cell_text = []
        row_headers = []
        for row in pending_jobs + finished_jobs:
            job = cast(MonteCarloJob, row[0])
            row_headers.append(job.hash[:6])
            cell_text.append([str(e) for e in row[1:]])
        if len(cell_text) == 0:
            return
        rcolors = []
        orange = plt.cm.Oranges(0.1)  # type: ignore
        for row in pending_jobs:
            rcolors.append(orange)
        rcolors.extend(["#FFFFFF"] * len(finished_jobs))
        the_table = ax.table(
            cellText=cell_text,
            rowLabels=row_headers,
            rowColours=rcolors,
            rowLoc="right",
            # colColours=ccolors,
            colLabels=column_headers,
            loc="center",
        )
        the_table.auto_set_column_width(list(range(len(row_headers))))
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_frame_on(False)
        self.hdisplay.update(fig)
