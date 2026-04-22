"""
Container runtime – Linux process isolation.

Uses unshare(1) to create new mount + PID namespaces,
then chroot(8) to pivot the process into the assembled rootfs.

Isolation strategy (tried in order):
  1. Unprivileged user namespace:
       unshare --user --map-root-user --mount --pid --fork chroot <rootfs>
     Works when kernel.apparmor_restrict_unprivileged_userns=0 (or the sysctl
     kernel.unprivileged_userns_clone=1 without AppArmor restriction).
  2. Privileged sudo fallback:
       sudo unshare --mount --pid --fork chroot <rootfs>
     Used automatically when the user-NS path fails due to AppArmor or other
     kernel restrictions (Ubuntu 24.04+).  Requires passwordless sudo or a
     one-time password prompt.

The SAME function is used for:
  • RUN instructions during build
  • docksmith run  (container start)

Requirements:
  • Linux kernel ≥ 3.12
  • unshare(1) and chroot(8) on host PATH  (util-linux, standard on all distros)
  • sudo access if unprivileged user namespaces are blocked by AppArmor

To permanently enable unprivileged user namespaces on Ubuntu 24.04+:
  sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
"""

import shlex
import subprocess
import sys
from pathlib import Path


# ── public API ────────────────────────────────────────────────────────────────

def run_isolated(
    rootfs: Path,
    cmd: list[str],
    env: dict[str, str],
    workdir: str = "/",
    *,
    stdin=None,
    stdout=None,
    stderr=None,
) -> int:
    """
    Run *cmd* inside *rootfs* with Linux namespace isolation.

    Tries unprivileged user-namespace path first, then falls back to
    sudo-based isolation automatically.

    Returns the process exit code.
    Raises RuntimeError if not on Linux or if both strategies fail.
    """
    if sys.platform != "linux":
        raise RuntimeError("Container runtime requires Linux.")

    _ensure_dirs(rootfs)
    inner_sh = _build_inner_script(env, workdir, cmd)

    # ── Strategy 1: unprivileged user namespace ───────────────────────────────
    cmd_unpriv = [
        "unshare",
        "--user",           # new user namespace
        "--map-root-user",  # map calling uid → root inside namespace
        "--mount",          # new mount namespace
        "--pid",            # new PID namespace
        "--fork",           # fork so child is PID 1 in new PID ns
        "chroot", str(rootfs),
        "/bin/sh", "-c", inner_sh,
    ]

    # Capture stderr on this first attempt so we can detect the uid_map error
    # without printing noise to the user.
    first = subprocess.run(
        cmd_unpriv,
        stdin=stdin,
        stdout=stdout,
        stderr=subprocess.PIPE,   # captured; re-emitted below if needed
    )
    if first.returncode == 0:
        return 0

    err_text = first.stderr.decode(errors="replace")
    _is_userns_blocked = (
        "uid_map" in err_text
        or ("Operation not permitted" in err_text and "unshare" in err_text)
        or "apparmor" in err_text.lower()
    )

    if not _is_userns_blocked:
        # Real container error – print stderr and return the code
        if stderr is None:
            sys.stderr.buffer.write(first.stderr)
        return first.returncode

    # ── Strategy 2: sudo + mount/pid namespace (no user NS needed) ───────────
    print(
        "[runtime] Unprivileged user namespaces are blocked on this system "
        "(AppArmor or kernel restriction).\n"
        "[runtime] Falling back to: sudo unshare --mount --pid --fork chroot\n"
        "[runtime] Tip: to fix permanently, run:\n"
        "[runtime]   sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0",
        file=sys.stderr,
    )

    cmd_sudo = [
        "sudo",
        "unshare",
        "--mount",   # new mount namespace
        "--pid",     # new PID namespace
        "--fork",    # fork so child is PID 1 in new PID ns
        "chroot", str(rootfs),
        "/bin/sh", "-c", inner_sh,
    ]

    second = subprocess.run(
        cmd_sudo,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
    return second.returncode


# ── helpers ───────────────────────────────────────────────────────────────────

def _ensure_dirs(rootfs: Path) -> None:
    """Create /proc and /tmp inside rootfs if missing (they may not exist in delta layers)."""
    for d in ("proc", "tmp", "dev"):
        (rootfs / d).mkdir(exist_ok=True, parents=True)


def _build_inner_script(
    env: dict[str, str],
    workdir: str,
    cmd: list[str],
) -> str:
    """
    Build the /bin/sh -c script that runs *inside* the chroot.

    Steps:
      1. Mount /proc (needed by many programs; ignore failure quietly).
      2. Export all ENV variables.
      3. cd to workdir.
      4. exec the target command (replaces the shell process).
    """
    parts: list[str] = [
        "mount -t proc proc /proc 2>/dev/null || true",
    ]

    # export env vars in deterministic order
    for k, v in sorted(env.items()):
        parts.append(f"export {k}={shlex.quote(v)}")

    wd = workdir if workdir else "/"
    parts.append(f"cd {shlex.quote(wd)} 2>/dev/null || cd /")

    cmd_str = " ".join(shlex.quote(c) for c in cmd)
    parts.append(f"exec {cmd_str}")

    return "; ".join(parts)
