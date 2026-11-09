"""Check that the upstream PR bundle still matches the local changes.

The bundle is exported by hand, so it silently rots: a new feature lands on the
working branch while ``upstream-pr`` and the exported patches keep describing
the previous state. Sending that would waste the author's time.

Run after any change that touches the PR paths:

    python docs/local-changes/verify-upstream-bundle.py

Exit code 0 means the branch and bundle are current; 1 lists what to fix.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

BASELINE = 'fa3e137'
BRANCH = 'upstream-pr'
# The branch that carries the day-to-day work. ``master`` tracks upstream since
# the fork split, so the series is compared against ``custom`` instead.
SOURCE = 'custom'
# Paths that belong in a pull request. docs/local-changes is local-only.
PR_PATHS = ('ballontranslator', 'doc', 'tests')
DEFAULT_BUNDLE = Path(r'H:\DSH\workbench\ball-upstream')


def git(*args: str) -> bytes:
    result = subprocess.run(
        ('git', *args),
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f'git {" ".join(args)} failed:\n'
            f'{result.stderr.decode("utf-8", "replace")}'
        )
    return result.stdout


def parse_args(argv: list[str]) -> tuple[Path, str, str, str]:
    bundle, branch, baseline, source = DEFAULT_BUNDLE, BRANCH, BASELINE, SOURCE
    rest = list(argv[1:])
    while rest:
        flag = rest.pop(0)
        if flag == '--branch' and rest:
            branch = rest.pop(0)
        elif flag == '--baseline' and rest:
            baseline = rest.pop(0)
        elif flag == '--source' and rest:
            source = rest.pop(0)
        elif flag == '--bundle' and rest:
            bundle = Path(rest.pop(0))
        elif not flag.startswith('-'):
            bundle = Path(flag)
        else:
            raise SystemExit(f'unknown argument: {flag}')
    return bundle, branch, baseline, source


def main(argv: list[str]) -> int:
    bundle, branch_name, baseline, source = parse_args(argv)
    problems: list[str] = []

    branches = git('branch', '--list', branch_name).decode()
    if branch_name not in branches:
        print(f'FAIL: branch {branch_name!r} is missing.')
        return 1

    source_branches = git('branch', '--list', source).decode()
    if source not in source_branches:
        print(f'FAIL: source branch {source!r} is missing.')
        return 1

    # 1. The branch must carry every change the working branch made to PR paths.
    drift = git('diff', '--stat', source, branch_name, '--', *PR_PATHS)
    if drift.strip():
        problems.append(
            f'{branch_name} is behind {source} on PR paths; rebuild it:\n'
            + drift.decode('utf-8', 'replace').rstrip()
        )

    # 2. The working branch must not touch PR paths in ways the branch lacks.
    only_source = git(
        'diff', '--name-only', branch_name, source, '--', *PR_PATHS
    )
    if only_source.strip():
        problems.append(
            f'{source} has PR-path changes missing from the branch:\n  '
            + '\n  '.join(only_source.decode().split())
        )

    # 3. full.diff must be byte-identical to the current series.
    expected = git('diff', f'{baseline}..{branch_name}', '--', *PR_PATHS)
    diff_path = bundle / 'full.diff'
    if not diff_path.is_file():
        problems.append(f'missing {diff_path}')
    else:
        actual = diff_path.read_bytes()
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
            problems.append(
                f'{diff_path} is stale '
                f'({len(actual)} bytes on disk, {len(expected)} expected)'
            )

    # 4. Each patch must come from a commit the series still contains.
    commits = git(
        'rev-list', '--reverse', f'{baseline}..{branch_name}'
    ).decode().split()
    patches = sorted(bundle.glob('*.patch'))
    if len(patches) != len(commits):
        problems.append(
            f'{len(patches)} patch file(s) for {len(commits)} commit(s)'
        )
    seen = set()
    for patch in patches:
        header = next(
            (line for line in patch.read_text('utf-8', 'replace').splitlines()
             if line.startswith('From ')),
            '',
        )
        sha = header[5:45]
        if len(sha) != 40:
            problems.append(f'{patch.name}: no commit header')
            continue
        if sha not in commits:
            problems.append(
                f'{patch.name}: exports {sha[:8]}, not in '
                f'{baseline}..{branch_name}'
            )
        seen.add(sha)
    for sha in commits:
        if sha not in seen:
            problems.append(f'commit {sha[:8]} has no exported patch')

    if problems:
        print('BUNDLE IS NOT CURRENT')
        for index, problem in enumerate(problems, 1):
            print(f'  {index}. {problem}')
        print(
            f'\nRebuild: git checkout -B {branch_name} {baseline}, '
            're-checkout the PR paths per feature commit, then '
            'git format-patch and git diff as described in '
            'docs/local-changes/0004-upstream-pr-bundle.md'
        )
        return 1

    print(
        f'OK: {len(commits)} commit(s), {len(patches)} patch(es), '
        f'full.diff matches, {branch_name} == {source} on '
        f'{", ".join(PR_PATHS)}'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
