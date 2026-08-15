import glob
from importlib import import_module, invalidate_caches
from pathlib import Path

import mythic_container

SKIP = {"__init__.py", "packaging.py", "aliases.py", "tasking.py"}

invalidate_caches()
search = Path(__file__).parent / "browserboy" / "agent_functions" / "*.py"
for path in glob.glob(str(search)):
    name = Path(path).name
    if name in SKIP:
        continue
    import_module("browserboy.agent_functions." + Path(path).stem)

mythic_container.mythic_service.start_and_run_forever()
