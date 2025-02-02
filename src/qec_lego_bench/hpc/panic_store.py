from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import os
import portalocker
import hjson
from .job_store import JobParameters
from typing import Optional


class PanicStore:

    def __init__(self, filename: str):
        assert filename is not None
        self.filename = filename
        self.store: dict[str, "JobPanic"] = {}

    def get_panic(self, *args, **kwargs) -> Optional["JobPanic"]:
        parameters = JobParameters(args, kwargs)
        if parameters.hash not in self.store:
            return None
        panic = self.store[parameters.hash]
        assert (
            parameters == panic.parameters
        ), f"hash conflict: {parameters} != {panic.parameters} but has same hash {parameters.hash}"
        return panic

    def __contains__(self, parameters: JobParameters) -> bool:
        return parameters.hash in self.store

    def has_panic(self, *args, **kwargs) -> bool:
        return self.get_panic(*args, **kwargs) is not None

    def add_panic(self, panic: "JobPanic") -> None:
        if panic.hash in self.store:
            # update panic
            stored_panic = self.store[panic.hash]
            assert (
                stored_panic.parameters == panic.parameters
            ), f"hash conflict: {stored_panic.parameters} != {panic.parameters} but has same hash {panic.hash}"
            stored_panic.latest = panic.latest
            stored_panic.panics.extend(panic.panics)
        else:
            self.store[panic.hash] = panic
        # save to file
        self.update_file()

    def load_from_file(self):
        if not os.path.exists(self.filename):
            return
        with portalocker.Lock(self.filename, "r") as f:
            persist = hjson.load(f)
            for hash, value in persist.items():
                panic = JobPanic.from_dict(value)
                self.store[panic.hash] = panic

    def update_file(self):
        with portalocker.Lock(
            self.filename, "r+" if os.path.exists(self.filename) else "w+"
        ) as f:
            content = f.read()
            if content == "":
                persist = {}
            else:
                persist = hjson.loads(content)
            f.seek(0)
            for panic in self.store.values():
                if panic.hash not in persist:
                    persist[panic.hash] = panic.to_dict()
                else:
                    # sanity check
                    entry = persist[panic.hash]
                    parameters = JobParameters.from_dict(entry["parameters"])
                    assert (
                        parameters == panic.parameters
                    ), f"Hash conflict: {parameters} != {panic.parameters} but has same hash {panic.hash}"
            hjson.dump(persist, f, indent=4)
            f.truncate()


@dataclass_json
@dataclass
class JobPanic:
    parameters: JobParameters
    latest: str  # record human-readable information of the latest panic
    panics: list[str] = field(default_factory=list)

    def __post__init(self):
        assert isinstance(self.parameters, JobParameters)

    @property
    def hash(self):
        return self.parameters.hash

    def add_panic(self, panic: str) -> "JobPanic":
        self.panics.append(panic)
        return self
