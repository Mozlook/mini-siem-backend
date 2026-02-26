import os


from handlers.exceptions import LogDirUnavailableError


def get_apps_from_fs(log_dir: str) -> list[str]:
    try:
        apps: list[str] = []
        with os.scandir(log_dir) as it:
            for entry in it:
                if entry.name.startswith("."):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    apps.append(entry.name)
        apps.sort(key=str.casefold)
        return apps
    except (FileNotFoundError, PermissionError) as e:
        raise LogDirUnavailableError(log_dir) from e
