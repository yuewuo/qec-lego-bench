from ..monte_carlo import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from IPython import display
from typing import cast
from dataclasses import field
from .logical_error_rate_plotter import closed_figure


@dataclass
class JobProgressPlotter:
    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)
    sort_by_name: bool = False
    finished_job_sort_by_name: bool = True  # otherwise sort by duration

    # to make sure the figure is large enough and the text is readable...
    min_rows: int = 30

    def __call__(
        self, executor: MonteCarloJobExecutor, show_logical_error: bool = True
    ):
        fig = self.fig
        ax = fig.gca()
        ax.clear()
        pending_jobs = []
        finished_jobs = []
        panic_jobs = []
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
                row = [
                    job,
                    repr(job),
                    f"{job.finished_shots}",
                    "-",
                    "-",
                    "-",
                    "-",
                    f"{job.duration:.1f}s ({job.duration/60:.1f}min)",
                ]
            else:
                submitted = job.pending_shots
                pending_submit = executor.pending_submit.get(job)
                if pending_submit is not None:
                    submitted -= pending_submit[0]
                job_future_percentage = 0.0
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
            if job.parameters in executor.panics:
                panic_jobs.append(row)
            elif job.pending_shots > 0:
                pending_jobs.append(row)
            else:
                finished_jobs.append(row)
        while len(pending_jobs) + len(finished_jobs) < self.min_rows:
            finished_jobs.append([MonteCarloJob()] + ["-"] * (len(column_headers)))
        # add colors to the jobs
        orange = plt.cm.Oranges(0.1)  # type: ignore
        red = plt.cm.Reds(0.5)  # type: ignore
        white = "#FFFFFF"
        colored_pending_jobs = [(orange, row) for row in pending_jobs]
        colored_panic_jobs = [(red, row) for row in panic_jobs]
        colored_finished_jobs = [(white, row) for row in finished_jobs]
        if self.sort_by_name:
            colored_jobs = (
                colored_pending_jobs + colored_panic_jobs + colored_finished_jobs
            )
            colored_jobs.sort(key=lambda e: e[1][1])
        else:
            colored_pending_jobs.sort(
                key=lambda e: -cast(MonteCarloJob, e[1][0]).duration
            )
            colored_finished_jobs.sort(
                key=(
                    (lambda e: e[1][1])
                    if self.finished_job_sort_by_name
                    else (lambda e: -cast(MonteCarloJob, e[1][0]).duration)
                )
            )
            colored_jobs = (
                colored_pending_jobs + colored_panic_jobs + colored_finished_jobs
            )
        cell_text = []
        row_headers = []
        for color, row in colored_jobs:
            job = cast(MonteCarloJob, row[0])
            row_headers.append(job.hash[:6])
            cell_text.append([str(e) for e in row[1:]])
        if len(cell_text) == 0:
            return
        rcolors = [e[0] for e in colored_jobs]
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
