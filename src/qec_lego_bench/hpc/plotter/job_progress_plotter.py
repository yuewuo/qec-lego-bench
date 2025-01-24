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

    def __call__(
        self, executor: MonteCarloJobExecutor, show_logical_error: bool = True
    ):
        fig: Figure = plt.figure()
        fig.clear()
        pending_jobs = []
        finished_jobs = []
        column_headers = [
            "Job",
            "Finished",
            "Pending",
            "Submitted",
            "Total",
            "Duration",
        ]
        if show_logical_error:
            column_headers.extend(["Errors", "Discards", "Error Rate"])
        for job in executor:
            if job.expecting_shots == 0:
                continue
            submitted = job.pending_shots
            pending_submit = executor.pending_submit.get(job)
            if pending_submit is not None:
                submitted -= pending_submit[0]
            row = [
                job,
                repr(job),
                f"{job.finished_shots} ({int(job.finished_shots/job.expecting_shots*100)}%)",
                f"{job.pending_shots} ({int(job.pending_shots/job.expecting_shots*100)}%)",
                f"{submitted} ({int(submitted/job.expecting_shots*100)}%)",
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
            plt.close(fig)
            return
        rcolors = []
        orange = plt.cm.Oranges(0.1)  # type: ignore
        for row in pending_jobs:
            rcolors.append(orange)
        rcolors.extend(["#FFFFFF"] * len(finished_jobs))
        the_table = plt.table(
            cellText=cell_text,
            rowLabels=row_headers,
            rowColours=rcolors,
            rowLoc="right",
            # colColours=ccolors,
            colLabels=column_headers,
            loc="center",
        )
        the_table.auto_set_column_width(list(range(len(row_headers))))
        ax = plt.gca()
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.box(on=None)
        self.hdisplay.update(fig)
        plt.close(fig)
