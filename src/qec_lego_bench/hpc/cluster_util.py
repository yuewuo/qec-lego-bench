from typing import Iterable, Tuple


def tmux_list_script(jobs: Iterable[Tuple[str, str]], prefix: str | None = None) -> str:
    script = "#!/bin/bash\n\n"
    if prefix is not None:
        script += f"# prefix start\n{prefix}\n# prefix end\n\n"
    for tmux_name, command in jobs:
        assert "'" not in command, "command should not contain single quotes"
        script += f'tmux new-session -d -s {tmux_name} "{command}"\n'
    return script
