"""Create an OS-specific distributable and include dependency license files."""
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "release-assets"
    output.mkdir(exist_ok=True)
    stage = ROOT / "build" / "release-stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    shutil.copy2(ROOT / "README.md", stage / "README.md")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.md")
    licenses = stage / "licenses"
    shutil.copytree(ROOT / "third-party-licenses", licenses)
    inventory = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"]
        inventory.append({"name": name, "version": distribution.version,
                          "license": distribution.metadata.get("License-Expression") or distribution.metadata.get("License"),
                          "project_urls": distribution.metadata.get_all("Project-URL") or []})
        for file in distribution.files or []:
            if any(word in str(file).lower() for word in ("license", "copying", "notice")):
                source = Path(distribution.locate_file(file))
                if source.is_file() and ".dist-info" in str(file):
                    relative = Path(*file.parts[1:])
                    destination = licenses / name / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    (licenses / "packages.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    if sys.platform == "darwin":
        shutil.copytree(ROOT / "dist/GemmaLocalSearch.app", stage / "GemmaLocalSearch.app", symlinks=True)
        (stage / "Applications").symlink_to("/Applications", target_is_directory=True)
        artifact = output / "GemmaLocalSearch-macOS-arm64.dmg"
        subprocess.run(["hdiutil", "create", "-volname", "Gemma Local Search", "-srcfolder", str(stage),
                        "-ov", "-format", "UDZO", str(artifact)], check=True)
    elif sys.platform == "win32":
        shutil.copytree(ROOT / "dist/GemmaLocalSearch", stage / "GemmaLocalSearch")
        artifact = Path(shutil.make_archive(str(output / "GemmaLocalSearch-Windows-x64"), "zip", stage))
    else:
        raise RuntimeError("Build on macOS ARM64 or Windows x64.")
    with artifact.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    artifact.with_suffix(artifact.suffix + ".sha256").write_text(f"{digest}  {artifact.name}\n", encoding="utf-8")
    print(artifact)


if __name__ == "__main__":
    main()
