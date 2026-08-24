$ErrorActionPreference = "Stop"
$old = '<a href="#">Methodology</a>'
$new = '<a href="methodology.html">Methodology</a>'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

$fixedCount = 0
Get-ChildItem *.html | ForEach-Object {
    $text = [System.IO.File]::ReadAllText($_.FullName)
    if ($text.Contains($old)) {
        $newText = $text.Replace($old, $new)
        [System.IO.File]::WriteAllText($_.FullName, $newText, $utf8NoBom)
        Write-Host "Fixed: $($_.Name)"
        $fixedCount++
    }
}

Write-Host ""
Write-Host "Done. Fixed $fixedCount files."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  git diff --stat"
Write-Host "  git diff <one file>"
Write-Host "  git add -A"
Write-Host "  git commit -m 'Fix dead Methodology nav link site-wide'"
Write-Host "  git push"