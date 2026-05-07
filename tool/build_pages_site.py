#!/usr/bin/env python3
"""Build the GitHub Pages artifact with encrypted report data.

Usage:
  REPORT_ACCESS_PASSWORD='...' python3 tool/build_pages_site.py --output public

The script writes a static site directory containing index.html plus encrypted
company-analysis YAML and Markdown files. Plain report data is intentionally not
copied into the output directory.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
from pathlib import Path

import yaml
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


ITERATIONS = 200_000


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(source: Path, dest: Path, key: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    iv = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(iv, source.read_bytes(), None)
    payload = {
        "version": 1,
        "algorithm": "AES-256-GCM",
        "iv": b64(iv),
        "ciphertext": b64(ciphertext),
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def copy_static_files(repo_root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / "index.html", output / "index.html")
    (output / ".nojekyll").write_text("", encoding="utf-8")


def recruitment_company_name(source: Path) -> str | None:
    try:
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    company = data.get("company")
    if not isinstance(company, dict):
        return None
    name = company.get("name")
    return name if isinstance(name, str) and name else None


def build_site(repo_root: Path, output: Path, password: str) -> None:
    if not password:
        raise SystemExit("REPORT_ACCESS_PASSWORD is required.")

    if output.exists():
        shutil.rmtree(output)
    copy_static_files(repo_root, output)

    source_root = repo_root / "report" / "company_analysis"
    data_root = source_root / "data"
    companies_root = source_root / "companies"
    output_root = output / "report" / "company_analysis"
    recruitment_data_root = repo_root / "report" / "recruitment-info" / "data"
    recruitment_output_root = output / "report" / "recruitment-info"

    salt = os.urandom(16)
    key = derive_key(password, salt)
    manifest = {
        "version": 1,
        "encrypted": True,
        "kdf": {
            "name": "PBKDF2",
            "hash": "SHA-256",
            "iterations": ITERATIONS,
            "salt": b64(salt),
        },
        "data": [],
        "recruitmentInfo": [],
    }

    for yaml_path in sorted(data_root.glob("*.yaml")):
        file_name = yaml_path.name
        stem = yaml_path.stem
        encrypted_data_path = output_root / "data" / f"{file_name}.enc"
        encrypt_file(yaml_path, encrypted_data_path, key)

        entry = {
            "fileName": file_name,
            "encryptedPath": f"report/company_analysis/data/{file_name}.enc",
        }
        report_path = companies_root / f"{stem}.md"
        if report_path.exists():
            encrypted_report_path = output_root / "companies" / f"{stem}.md.enc"
            encrypt_file(report_path, encrypted_report_path, key)
            entry["encryptedReportPath"] = f"report/company_analysis/companies/{stem}.md.enc"

        manifest["data"].append(entry)

    if not manifest["data"]:
        raise SystemExit(f"No YAML files found in {data_root}")

    if recruitment_data_root.exists():
        for yaml_path in sorted(recruitment_data_root.glob("*.yaml")):
            file_name = yaml_path.name
            encrypted_data_path = recruitment_output_root / "data" / f"{file_name}.enc"
            encrypt_file(yaml_path, encrypted_data_path, key)
            entry = {
                "fileName": file_name,
                "encryptedPath": f"report/recruitment-info/data/{file_name}.enc",
            }
            company_name = recruitment_company_name(yaml_path)
            if company_name:
                entry["companyName"] = company_name
            manifest["recruitmentInfo"].append(entry)

    (output_root).mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="public", help="Output directory for the Pages artifact.")
    parser.add_argument(
        "--password",
        default=os.environ.get("REPORT_ACCESS_PASSWORD", ""),
        help="Access password. Prefer REPORT_ACCESS_PASSWORD in CI.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    build_site(repo_root, repo_root / args.output, args.password)


if __name__ == "__main__":
    main()
