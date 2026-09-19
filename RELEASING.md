# Releasing bazi

The manual `release.yml` workflow prepares one verified sdist and its rebuilt
wheel. The direct wheel is only a validation control. There are no push/tag
publication triggers and no arbitrary ref, registry or artifact inputs.

## Prerequisites

The owner must separately confirm PyPI account/project eligibility for `bazi` and
configure a Trusted Publisher (or pending publisher) for owner `0xf3cd`, repository
`bazi`, workflow `release.yml`, environment `release`. A public name lookup does not
reserve the name or establish account readiness. No API token belongs in this repository.

Create the GitHub environment `release` explicitly, with at least one required
reviewer and a custom deployment policy containing exactly branch `main` (not a
tag or wildcard). Personal owner approval is valid; allow self-review if that is
the intended approval path. This workflow does not require two people. Only the
publishing jobs bind the environment; an earlier read-only REST preflight fails
closed if the environment, reviewer rule or exact branch policy is missing.

The workflow must exist on the default branch before it can be dispatched.

## Rehearsal

1. Review `pyproject.toml`'s static version and `RELEASE_NOTES.md`. Merge the intended
   release changes to main before dispatch; do not create a tag yet.
2. Dispatch `Prepare or Publish Release` on main with `mode=rehearsal` (the default).
   This runs the full source and artifact gates at the dispatch SHA, with no
   environment binding, write permission or OIDC permission.
3. Inspect the run's `tested-release` artifact: exactly one wheel and sdist under
   `dist/`, release notes, `release.json`, and `SHA256SUMS`. Confirm the source SHA,
   run ID, version, licenses, file contents and checksums. Artifacts expire after
   30 days; retain the approved bytes before expiry when recovery may be needed.

Run a rehearsal before authorizing real publication. Local artifact and offline
policy tests do not substitute for it or prove GitHub/PyPI configuration is ready.

## Real Release

1. Obtain separate authorization and dispatch main with `mode=release`. Confirm
   that the dispatch SHA is the intended release commit. The real run performs its
   own full verification; it never accepts an artifact ID from a previous run.
2. Approve the protected environment for PyPI after checking the run's verified
   bundle. The OIDC-only job downloads the exact immutable artifact ID produced by
   this run, verifies checksums and identity, and rejects existing versions/tags/releases.
3. After PyPI succeeds, approve the GitHub Release job. This contents-write-only job
   checks PyPI hashes, creates `v<version>` at the tested SHA, creates a draft release,
   uploads the same bytes and notices, checks asset digests, then publishes the draft.
   Neither privileged job checks out, builds, installs or imports repository code.
4. Independently download both published artifacts from PyPI and GitHub and compare
   them to the retained checksums. Confirm the tag SHA and release metadata. Install
   the published wheel in a fresh environment and repeat the consumer smoke.
   Verify the actual PyPI Trusted Publisher identity/attestations too.

## Partial Failure

Publication is not transactional. An existing version, tag or release is an error;
there is no overwrite, tag move or `skip-existing` recovery. Do not rerun the whole
workflow to bypass a partial failure and do not rebuild the accepted bytes.

If PyPI has the pair but GitHub failed, stop and inspect the retained same-run
bundle, PyPI digests, tag SHA and any draft release/assets. The owner must approve
a targeted recovery of only the missing operations using those exact bytes. If a
tag or draft already exists, verify it rather than moving or replacing it. A digest
mismatch requires investigation, not automatic deletion, a version bump or a new upload.
