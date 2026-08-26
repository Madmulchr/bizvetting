# Adds a computed, data-driven paragraph to each individual deal page
# (deal-*.html), giving every listing genuinely unique free text instead
# of the current boilerplate that's word-for-word identical across all
# 345 pages except the grade letter. This is the fix for the thin-content
# SEO finding logged 2026-08-23/25 -- every number in the new paragraph
# is computed from data already on the page (or in listings.html), using
# the site's own already-locked underwriting assumptions from
# methodology.html (12.5% down, 9.5% rate, 10-year term). Nothing is
# hand-written or guessed, so nothing needs a human to re-verify it and
# nothing goes stale on its own.
#
# What it adds, using a real listing as an example (your real numbers
# will differ per page):
#   "At the midpoint of the asking price band ($325,000), a buyer
#   putting 12.5% down would need roughly $40,625 in cash and could
#   expect an estimated monthly SBA note payment near $3,680 (9.5%
#   rate, 10-year term). By stressed DSCR, this listing ranks 47th of
#   333 in the current batch (1st = strongest cash-flow cushion after
#   the stress test)."
#
# IMPORTANT -- keep these three numbers in sync with methodology.html:
# if the down-payment %, note rate, or term ever change there, update
# the $DOWN_PCT / $RATE_ANNUAL / $TERM_MONTHS constants below to match,
# or this script will start computing against stale assumptions. The
# sentence wording ("12.5% down", "9.5% rate, 10-year term") is derived
# from these constants at run time, not hardcoded separately -- so
# updating the three constants is the only edit needed.
#
# Safe to re-run: it marks its own paragraph with an HTML comment and
# replaces just that block on a second run, instead of adding a
# duplicate. Re-run any time listing data changes (new cycle, a region
# or price fix, etc.) to keep the numbers current -- it will NOT do
# that automatically, only when you run it.
#
# HOW TO RUN:
# 1. Open PowerShell.
# 2. cd C:\dev\bizvetting-repo
# 3. .\add-deal-computed-content.ps1
# 4. Read the output -- one line per page it updated, with the key
#    computed numbers, plus a total count and a list of anything
#    skipped (skipped pages are named explicitly rather than guessed at).
# 5. git diff --stat
#    git diff deal-midwest-mi-hvac-grade-a-1-6x-sde-a2a67565.html   (spot check)
#    git add -A
#    git commit -m "Add computed financing paragraph to deal pages"
#    git push

$ErrorActionPreference = "Stop"
$repoDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($repoDir)) { $repoDir = (Get-Location).Path }
Set-Location -Path $repoDir
[Environment]::CurrentDirectory = $repoDir
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# ---- Assumptions -- must match methodology.html verbatim ----
$DOWN_PCT = 0.125
$RATE_ANNUAL = 0.095
$TERM_MONTHS = 120

$markerStart = '<!-- BV-COMPUTED-CONTENT-START -->'
$markerEnd = '<!-- BV-COMPUTED-CONTENT-END -->'
$ctaPara = '<p>Full listing details, including the exact asking price, target-offer price, and a direct link to the original listing, are available to members.</p>'

function Parse-Money($s) {
    $s = $s.Trim()
    if ($s -match '^\$([0-9.]+)M$') { return [double]$matches[1] * 1000000 }
    if ($s -match '^\$([0-9.]+)K$') { return [double]$matches[1] * 1000 }
    return $null
}

function Format-Dollars([double]$n) {
    return "`$" + ("{0:N0}" -f $n)
}

function Get-Ordinal([int]$n) {
    $rem100 = $n % 100
    if ($rem100 -ge 11 -and $rem100 -le 13) { return "$($n)th" }
    switch ($n % 10) {
        1 { return "$($n)st" }
        2 { return "$($n)nd" }
        3 { return "$($n)rd" }
        default { return "$($n)th" }
    }
}

# ---- Pass 1: build the full batch's stressed-DSCR distribution from listings.html ----
# (Ineligible rows -- e.g. "Exceeds SBA $5M loan cap" -- have no <span class="stressed">
# and no real deal page, so this regex naturally excludes them without special-casing.)
if (-not (Test-Path 'listings.html')) {
    Write-Host "ERROR: listings.html not found in $repoDir -- aborting."
    exit 1
}
$listingsText = [System.IO.File]::ReadAllText((Join-Path $repoDir 'listings.html'))
$dscrRx = [regex]::new('class="stressed">([0-9.]+)</span>')
$allDscr = @()
foreach ($m in $dscrRx.Matches($listingsText)) {
    $allDscr += [double]$m.Groups[1].Value
}
$totalBatch = $allDscr.Count
if ($totalBatch -eq 0) {
    Write-Host "ERROR: parsed 0 listings from listings.html -- aborting rather than computing against an empty batch."
    exit 1
}
Write-Host "Batch loaded from listings.html: $totalBatch eligible listings."
Write-Host ""

# ---- Pass 2: process every deal page ----
$rxOpts = [System.Text.RegularExpressions.RegexOptions]::Singleline
$priceRx = [regex]::new('Asking price band</th><td>(\$[0-9.]+[KM]) . (\$[0-9.]+[KM])</td>')
$ownDscrRx = [regex]::new('DSCR . stressed.*?</th><td>([0-9.]+)</td>', $rxOpts)
# Built as a separate variable, not inline -- New-Object regex(a + b, $opts) has a real
# PowerShell parsing bug where the options argument silently gets absorbed into the
# pattern string instead of passed separately. [regex]::new(...) with a precomputed
# pattern avoids it entirely. (Same bug exists in add-hub-batch-stats.ps1's
# $existingBlockPattern -- flagged separately, not touched here.)
$existingBlockPattern = ([regex]::Escape($markerStart)) + '.*?' + ([regex]::Escape($markerEnd))
$existingBlockRx = [regex]::new($existingBlockPattern, $rxOpts)

$dealFiles = Get-ChildItem deal-*.html
$updatedCount = 0
$skipped = @()

foreach ($file in $dealFiles) {
    $text = [System.IO.File]::ReadAllText($file.FullName)

    $priceM = $priceRx.Match($text)
    $dscrM = $ownDscrRx.Match($text)

    if (-not $priceM.Success -or -not $dscrM.Success) {
        $skipped += "$($file.Name)  (could not parse price band or stressed DSCR)"
        continue
    }
    if ($text -notmatch [regex]::Escape($ctaPara)) {
        $skipped += "$($file.Name)  (expected 'Full listing details...members' paragraph not found -- page structure differs)"
        continue
    }

    $lo = Parse-Money $priceM.Groups[1].Value
    $hi = Parse-Money $priceM.Groups[2].Value
    if ($null -eq $lo -or $null -eq $hi) {
        $skipped += "$($file.Name)  (price band did not parse to numbers)"
        continue
    }

    $mid = ($lo + $hi) / 2
    $down = $mid * $DOWN_PCT
    $loan = $mid - $down
    $r = $RATE_ANNUAL / 12
    $pmt = $loan * $r * [math]::Pow(1 + $r, $TERM_MONTHS) / ([math]::Pow(1 + $r, $TERM_MONTHS) - 1)

    $ownDscr = [double]$dscrM.Groups[1].Value
    $betterCount = ($allDscr | Where-Object { $_ -gt $ownDscr }).Count
    $rank = $betterCount + 1
    $ordinalRank = Get-Ordinal $rank

    $downStr = Format-Dollars $down
    $pmtStr = Format-Dollars $pmt
    $midStr = Format-Dollars $mid
    # Derived from the constants, not hardcoded, so changing DOWN_PCT/RATE_ANNUAL/
    # TERM_MONTHS above automatically keeps the sentence wording in sync -- no
    # second place to remember to edit.
    $downPctStr = ("{0:0.#}" -f ($DOWN_PCT * 100)) + "%"
    $ratePctStr = ("{0:0.#}" -f ($RATE_ANNUAL * 100)) + "%"
    $termYears = $TERM_MONTHS / 12

    $sentence = "At the midpoint of the asking price band ($midStr), a buyer putting $downPctStr down would need roughly $downStr in cash and could expect an estimated monthly SBA note payment near $pmtStr ($ratePctStr rate, $termYears-year term). By stressed DSCR, this listing ranks $ordinalRank of $totalBatch in the current batch (1st = strongest cash-flow cushion after the stress test)."

    $newPara = "<p>$sentence</p>"
    $insertBlock = "$markerStart`n      $newPara`n      $markerEnd"

    if ($text -match [regex]::Escape($markerStart)) {
        $newText = $existingBlockRx.Replace($text, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $insertBlock }, 1)
    } else {
        $newText = $text.Replace($ctaPara, "$insertBlock`n      $ctaPara")
    }

    if ($newText -ne $text) {
        [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8NoBom)
        Write-Host "Updated: $($file.Name)  (mid $midStr, down $downStr, pmt $pmtStr/mo, DSCR rank $rank of $totalBatch)"
        $updatedCount++
    }
}

Write-Host ""
Write-Host "Done. Updated $updatedCount of $($dealFiles.Count) deal pages."
if ($skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "SKIPPED ($($skipped.Count)):"
    foreach ($s in $skipped) { Write-Host "  $s" }
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "  git diff --stat"
Write-Host "  git diff deal-midwest-mi-hvac-grade-a-1-6x-sde-a2a67565.html    (spot check the new paragraph reads correctly)"
Write-Host "  git add -A"
Write-Host "  git commit -m 'Add computed financing paragraph to deal pages'"
Write-Host "  git push"