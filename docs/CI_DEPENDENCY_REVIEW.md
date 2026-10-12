# Workbook dependency setup — execution-only infrastructure amendment

The result commit `67f3cfab1631e94bcd1849fa9b23ab729ad8a337` passes all 74
repository tests, the complete new-calibration audit and the existing predictive
regression. Its benefits workflow run 38236183553 stalled for more than 16 minutes
at `sudo apt-get update -qq`, before LibreOffice installation or recalculation.
The live job page showed only that package-index command; the recalculation
must not be reported as passed. The superseded run was cancelled.

The workflow now uses an existing LibreOffice installation when available,
otherwise tries the runner's package cache before a bounded index refresh and
retry. Network operations have 20-second acquisition timeouts, one retry,
IPv4 acquisition and 180-second process limits. The whole recalculation step
has a 12-minute limit. Optional recommended packages are not required, but
LibreOffice Calc and its required dependencies still must install successfully.
The installed LibreOffice version is recorded. No package mirror, certificate
validation, permission or workbook assertion is weakened.

Every original model, RAA calculation, published-cache check, rebuilt
formula/input comparison, LibreOffice conversion, recalculated-cache check and
artifact upload remains required. The frozen workbook, public data, old and
new study outputs, registered mathematical implementations, protocol and
independent checker are unchanged. This is dependency handling, not a new
empirical result or a recalibration. A matching-head successful workflow must
include the actual LibreOffice recalculation and final workbook verification.

Reference: [Debian APT configuration manual](https://manpages.debian.org/bookworm/apt/apt.conf.5.en.html)
and [APT command manual](https://manpages.debian.org/bookworm/apt/apt-get.8.en.html).
