import subprocess
from pathlib import Path


SECURE_DIR = Path.home() / "KHAGATARA-SECURE"

CLIENT_ID_FILE = SECURE_DIR / "lwa-client-id.txt"
CLIENT_SECRET_FILE = SECURE_DIR / "lwa-client-secret.dpapi"
REFRESH_TOKEN_FILE = SECURE_DIR / "sandbox-refresh-token.dpapi"


def _decrypt_dpapi_file(path: Path) -> str:
    encrypted = path.read_text(encoding="utf-8").strip()

    command = (
        "$secure = ConvertTo-SecureString -String "
        + f"'{encrypted}'; "
        "$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure); "
        "try { "
        "[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) "
        "} finally { "
        "[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) "
        "}"
    )

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error = result.stderr.strip()
        raise RuntimeError(
            f"Unable to decrypt {path.name}: {error}"
        )

    value = result.stdout.strip()

    if not value:
        raise RuntimeError(
            f"Unable to decrypt credential file: {path.name}"
        )

    return value


def get_client_id() -> str:
    return CLIENT_ID_FILE.read_text(encoding="utf-8").strip()


def get_client_secret() -> str:
    return _decrypt_dpapi_file(CLIENT_SECRET_FILE)


def get_refresh_token() -> str:
    return _decrypt_dpapi_file(REFRESH_TOKEN_FILE)