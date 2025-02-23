from ..monte_carlo import *
from IPython import display
from typing import cast
from dataclasses import field
import pandas as pd


@dataclass
class JobProgressPlotter:
    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    sort_by_name: bool = False
    finished_job_sort_by_name: bool = True  # otherwise sort by duration

    def __call__(
        self, executor: MonteCarloJobExecutor, show_logical_error: bool = True
    ):
        pending_jobs = []
        finished_jobs = []
        panic_jobs = []
        column_headers = [
            "Status",
            "JobKey",
            "Job",
            "Finished",
            "Pending",
            "Submitted",
            f"{len(executor.pending_futures)} jobs",
            "Total",
            "Duration",
        ]
        if show_logical_error:
            column_headers.extend(["Errors", "Discards", "Panics", "Error Rate"])
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
                    result = cast(LogicalErrorResult, job.result)
                    stats = result.stats_of(job)  # type: ignore
                    row.extend(
                        [
                            result.errors,
                            result.discards,
                            result.panics,
                            f"{stats.failure_rate:.1uS}",
                        ]
                    )
                else:
                    row.extend(["-", "-", "-", "-"])
            if job.parameters in executor.panics:
                panic_jobs.append(row)
            elif job.pending_shots > 0:
                pending_jobs.append(row)
            else:
                finished_jobs.append(row)
        # add status to the jobs
        pending_jobs = [["pending"] + row for row in pending_jobs]
        panic_jobs = [["panicked"] + row for row in panic_jobs]
        finished_jobs = [["finished"] + row for row in finished_jobs]
        if self.sort_by_name:
            jobs = pending_jobs + panic_jobs + finished_jobs
            jobs.sort(key=lambda e: e[2])  # type: ignore
        else:
            pending_jobs.sort(key=lambda e: -cast(MonteCarloJob, e[1]).duration)
            finished_jobs.sort(
                key=(
                    (lambda e: e[2])
                    if self.finished_job_sort_by_name
                    else (lambda e: -cast(MonteCarloJob, e[1]).duration)
                )
            )
            jobs = pending_jobs + panic_jobs + finished_jobs
        if len(jobs) == 0:
            return
        data: dict = {header: [] for header in column_headers}
        for row in jobs:
            job = cast(MonteCarloJob, row[1])
            text_row = [row[0], job.hash[:6]] + [str(e) for e in row[2:]]
            assert len(text_row) == len(column_headers)
            for header, element in zip(column_headers, text_row):
                data[header].append(element)

        # do not hide any rows or columns
        original_max_rows = pd.get_option("display.max_rows")
        original_max_columns = pd.get_option("display.max_columns")
        original_max_colwidth = pd.get_option("display.max_colwidth")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_colwidth", None)

        df = pd.DataFrame(data)
        dfStyler = df.style.set_properties(
            subset=["Status", "Job"], **{"text-align": "left"}
        )
        dfStyler.set_table_styles(
            [dict(selector="th", props=[("text-align", "center")])]
        )
        self.hdisplay.update(dfStyler)
        del dfStyler
        del df

        # recover max rows and columns
        pd.set_option("display.max_columns", original_max_columns)
        pd.set_option("display.max_rows", original_max_rows)
        pd.set_option("display.max_colwidth", original_max_colwidth)
