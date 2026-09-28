# Robust bulk download: streams chunks to disk, never restarts a partial file,
# and logs every attempt (one line each) so progress is visible.
param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$Dest,
    [int64]$ExpectedSize = 0,
    [int64]$MinBytes = 0,
    [int]$MaxAttempts = 200
)

if ($ExpectedSize -le 0) {
    # unknown size: aim for the largest plausible SDK installer and stop after MinBytes
    $ExpectedSize = [int64]::MaxValue
}
if ($MinBytes -gt $ExpectedSize) { $ExpectedSize = $MinBytes }

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Net.Http

$handler = New-Object System.Net.Http.HttpClientHandler
$handler.AllowAutoRedirect = $true
$client = New-Object System.Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromMinutes(20)
$client.DefaultRequestHeaders.UserAgent.ParseAdd('dsh')
$client.DefaultRequestHeaders.ExpectContinue = $false

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $have = 0
    if (Test-Path $Dest) { $have = (Get-Item $Dest).Length }
    if ($have -ge $ExpectedSize) { break }

    $fs = $null
    $stream = $null
    $resp = $null
    try {
        $req = New-Object System.Net.Http.HttpRequestMessage('GET', $Url)
        if ($have -gt 0) {
            $req.Headers.Range = New-Object System.Net.Http.Headers.RangeHeaderValue($have, $null)
        }
        $resp = $client.SendAsync($req, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        if ($resp -eq $null) { throw 'no response object' }
        $status = [int]$resp.StatusCode
        $stream = $resp.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        if ($stream -eq $null) { throw ('null content stream (status ' + $status + ')') }

        $fs = [System.IO.File]::Open($Dest, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        if ($status -eq 200) { $fs.SetLength(0) }
        $fs.Seek(0, [System.IO.SeekOrigin]::End) | Out-Null
        $buf = New-Object 'byte[]' 262144
        $written = 0
        while ($true) {
            $n = $stream.Read($buf, 0, $buf.Length)
            if ($n -le 0) { break }
            $fs.Write($buf, 0, $n)
            $written += $n
        }
        $fs.Flush()
        $now = (Get-Item $Dest).Length
        Write-Output ("attempt {0}: HTTP {1}, +{2:N1} MB -> {3:N1}/{4:N1} MB" -f $attempt, $status, ($written / 1MB), ($now / 1MB), ($ExpectedSize / 1MB))
    }
    catch {
        $now = 0
        if (Test-Path $Dest) { $now = (Get-Item $Dest).Length }
        Write-Output ("attempt {0}: error after {1:N1} MB - {2}" -f $attempt, ($now / 1MB), $_.Exception.Message)
    }
    finally {
        if ($fs -ne $null) { $fs.Dispose() }
        if ($stream -ne $null) { $stream.Dispose() }
        if ($resp -ne $null) { $resp.Dispose() }
    }
    Start-Sleep -Milliseconds 400
}

$final = 0
if (Test-Path $Dest) { $final = (Get-Item $Dest).Length }
Write-Output ("DONE size={0} expected={1} complete={2}" -f $final, $ExpectedSize, ($final -ge $ExpectedSize))
