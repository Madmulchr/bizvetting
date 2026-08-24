# Adds a computed, data-driven summary paragraph to each hub page
# (hub-*.html), right under the existing one-line intro. Every number
# in the new paragraph is computed from that page's own listing table --
# nothing is hand-written or guessed, so nothing needs to be re-verified
# by a human and nothing goes stale on its own (see notes at the bottom
# for what "stale" means here and when to re-run this).
#
# What it adds, using Utah as an example of the kind of sentence this
# produces (your real numbers will differ per page):
#   "Within this batch, asking prices span $200K to $3.5M and stressed
#   DSCR ranges from 1.06x to 2.91x (median 1.57x). 3 of 4 clear the
#   standard 1.25x SBA lender comfort threshold at the asking price as
#   stated; 1 would need a price reduction to get there."
#
# Safe to re-run: it marks its own paragraph with an HTML comment and
# replaces just that block on a second run, instead of adding a
# duplicate. Re-run this any time the listing data in a hub page
# changes (new cycle, a region fix, etc.) to keep the numbers current --
# it will NOT do that automatically, only when you run it.
#
# HOW TO RUN:
# 1. Open PowerShell.
# 2. cd C:\dev\bizvetting-repo
# 3. .\add-hub-batch-stats.ps1
# 4. Read the output -- one line per page it updated, with a quick
#    summary of what it computed, plus a total count at the end
#    (there are 46 hub-*.html files, so expect close to 46 -- fewer only
#    if the run is finding pages it can't confidently parse, which it
#    will skip and name explicitly rather than guess).
# 5. Same as before: git diff --stat, spot-check one file's diff, then
#    git add -A / commit / push.

$ErrorActionPreference = "Stop"
$repoDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($repoDir)) { $repoDir = (Get-Location).Path }
Set-Location -Path $repoDir
[Environment]::CurrentDirectory = $repoDir
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$markerStart = '<!-- BV-BATCH-STATS-START -->'
$markerEnd = '<!-- BV-BATCH-STATS-END -->'

function Parse-Money($s) {
    $s = $s.Trim()
    if ($s -match '^\$([0-9.]+)M$') { return [double]$matches[1] * 1000000 }
    if ($s -match '^\$([0-9.]+)K$') { return [double]$matches[1] * 1000 }
    return $null
}

function Format-Money([double]$n) {
    if ($n -ge 1000000) {
        $v = $n / 1000000
        $s = ("{0:0.##}" -f $v)
        return "`$$s" + "M"
    } else {
        $v = $n / 1000
        $s = ("{0:0}" -f $v)
        return "`$$s" + "K"
    }
}

$rxOpts = [System.Text.RegularExpressions.RegexOptions]::Singleline
$tablePattern = New-Object regex('<table class="ledger-table">.*?</table>', $rxOpts)
$rowPattern = New-Object regex('<tr[^>]*>.*?</tr>', $rxOpts)
$pricePattern = New-Object regex('class="num-cell">(\$[0-9.]+[KM]) . (\$[0-9.]+[KM])')
$dscrPattern = New-Object regex('class="stressed">([0-9.]+)</span>')
$batchSubPattern = New-Object regex('(<p class="batch-sub">.*?</p>)', $rxOpts)
$existingBlockPattern = New-Object regex(([regex]::Escape($markerStart)) + '.*?' + ([regex]::Escape($markerEnd)), $rxOpts)

$hubFiles = Get-ChildItem hub-*.html
$updatedCount = 0
$skippedCount = 0

foreach ($file in $hubFiles) {
    $text = [System.IO.File]::ReadAllText($file.FullName)

    $tableMatch = $tablePattern.Match($text)
    if (-not $tableMatch.Success) {
        Write-Host "SKIPPED (no ledger table found): $($file.Name)"
        $skippedCount++
        continue
    }
    $tableText = $tableMatch.Value

    $rows = $rowPattern.Matches($tableText) | Where-Object { $_.Value -match 'deal-title-cell' }

    $prices = @()
    $dscrStressed = @()
    $clears = 0
    $total = 0

    foreach ($row in $rows) {
        $rowText = $row.Value
        if ($rowText -match 'ineligible-row') { continue }
        $total++

        $pm = $pricePattern.Match($rowText)
        if ($pm.Success) {
            $lo = Parse-Money $pm.Groups[1].Value
            $hi = Parse-Money $pm.Groups[2].Value
            if ($null -ne $lo) { $prices += $lo }
            if ($null -ne $hi) { $prices += $hi }
        }

        $dm = $dscrPattern.Match($rowText)
        if ($dm.Success) {
            $dscrStressed += [double]$dm.Groups[1].Value
        }

        if ($rowText -match 'Clears at ask') { $clears++ }
    }

    if ($total -eq 0 -or $prices.Count -eq 0 -or $dscrStressed.Count -eq 0) {
        Write-Host "SKIPPED (couldn't parse listing rows): $($file.Name)"
        $skippedCount++
        continue
    }

    $priceMin = ($prices | Measure-Object -Minimum).Minimum
    $priceMax = ($prices | Measure-Object -Maximum).Maximum
    $dscrMin = ($dscrStressed | Measure-Object -Minimum).Minimum
    $dscrMax = ($dscrStressed | Measure-Object -Maximum).Maximum
    $dscrSorted = $dscrStressed | Sort-Object
    $mid = [math]::Floor($dscrSorted.Count / 2)
    if ($dscrSorted.Count % 2 -eq 0) {
        $dscrMedian = ([double]$dscrSorted[$mid-1] + [double]$dscrSorted[$mid]) / 2
    } else {
        $dscrMedian = [double]$dscrSorted[$mid]
    }
    $dscrMedian = [math]::Round($dscrMedian, 2)

    $priceMinStr = Format-Money $priceMin
    $priceMaxStr = Format-Money $priceMax

    if ($clears -eq $total) {
        $clearsSentence = "All $total clear the standard 1.25x SBA lender comfort threshold at the asking price as stated."
    } elseif ($clears -eq 0) {
        $clearsSentence = "None of the $total clear the standard 1.25x SBA lender comfort threshold at the asking price as stated -- every one would need a price reduction to get there."
    } else {
        $needs = $total - $clears
        $clearsSentence = "$clears of $total clear the standard 1.25x SBA lender comfort threshold at the asking price as stated; $needs would need a price reduction to get there."
    }

    $newPara = "<p class=`"batch-sub`">Within this batch, asking prices span $priceMinStr to $priceMaxStr and stressed DSCR ranges from ${dscrMin}x to ${dscrMax}x (median ${dscrMedian}x). $clearsSentence</p>"
    $insertBlock = "$markerStart`n$newPara`n$markerEnd"

    if ($text -match [regex]::Escape($markerStart)) {
        $newText = $existingBlockPattern.Replace($text, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $insertBlock }, 1)
    } else {
        $newText = $batchSubPattern.Replace($text, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $m.Value + "`n" + $insertBlock }, 1)
    }

    if ($newText -ne $text) {
        [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8NoBom)
        Write-Host "Updated: $($file.Name)  ($total listings, price $priceMinStr-$priceMaxStr, DSCR $dscrMin-$dscrMax, median $dscrMedian)"
        $updatedCount++
    }
}

Write-Host ""
Write-Host "Done. Updated $updatedCount of $($hubFiles.Count) hub pages. Skipped: $skippedCount."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  git diff --stat"
Write-Host "  git diff hub-utah.html    (or any other file -- spot check the new paragraph reads correctly)"
Write-Host "  git add -A"
Write-Host "  git commit -m 'Add computed batch-stats paragraph to hub pages'"
Write-Host "  git push"