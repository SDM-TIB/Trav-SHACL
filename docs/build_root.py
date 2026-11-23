#!/usr/bin/env python3
"""Post-processing of the multi-version build in build/html.

* Finds the newest release (e.g., v0.25.0).
* Publishes a copy of it as /latest/, a stable URL that always serves the newest release
  (also for future releases, as the copy is regenerated on every build).
* For every HTML page of the latest release, writes a redirect stub at the same path in the
  site root, so that old, unversioned URLs (e.g., /changelog.html) keep working and
  redirect to the same page below /latest/.
* Copies objects.inv to the root, so that intersphinx mappings to the unversioned URL keep working.
* Adds .nojekyll.
"""
import re
import shutil
from pathlib import Path

here = Path(__file__).parent
root = here / 'build' / 'html'
template = (here / '_templates' / 'redirect.html').read_text()


def version_key(tag: str):
    return tuple(int(x) for x in tag[1:].split('.'))


tags = sorted((d.name for d in root.iterdir() if d.is_dir() and re.fullmatch(r'v\d+\.\d+\.\d+', d.name)),
              key=version_key)
if not tags:
    raise SystemExit('No release docs found in build/html')
newest = tags[-1]

# stable URL for the newest release
latest_dir = root / 'latest'
if latest_dir.exists():
    shutil.rmtree(latest_dir)
shutil.copytree(root / newest, latest_dir)

# redirect stubs for the former unversioned pages
count = 0
for page in latest_dir.rglob('*.html'):
    rel = page.relative_to(latest_dir)
    stub = root / rel
    stub.parent.mkdir(parents=True, exist_ok=True)
    # a stub in a subdirectory needs a path relative to that directory
    target = '../' * (len(rel.parts) - 1) + f'latest/{rel.as_posix()}'
    stub.write_text(template.replace('{{ target }}', target))
    count += 1

if (latest_dir / 'objects.inv').exists():
    shutil.copy(latest_dir / 'objects.inv', root / 'objects.inv')
(root / '.nojekyll').touch()
print(f'Newest release: {newest} (copied to latest/); {count} redirect stubs written; versions: {", ".join(tags)}')
