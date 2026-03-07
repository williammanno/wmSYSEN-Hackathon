"""Copy Vite build output into backend/static for single-app deployment."""

from pathlib import Path
import shutil


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    frontend_dist = repo_root / "dashboard" / "dist"
    backend_static = repo_root / "backend" / "static"

    if not frontend_dist.exists():
        raise SystemExit(
            "Frontend build not found. Run `npm run build` in `dashboard/` first."
        )

    if backend_static.exists():
        shutil.rmtree(backend_static)

    shutil.copytree(frontend_dist, backend_static)
    print(f"Copied {frontend_dist} -> {backend_static}")


if __name__ == "__main__":
    main()
