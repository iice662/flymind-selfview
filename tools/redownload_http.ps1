"""Download with System.Net.Http (a different TLS stack than curl) and compare the
result byte-for-byte against the curl copy, to tell corruption in transit apart
from a genuinely malformed upstream file.

Windows PowerShell 5.1 compatible (no bitshift operators, no PS7 syntax).
"""
$ErrorActionPreference = 'Stop'
$url = 'https://ghfast.top/https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/Connectivity_783.parquet'
$dst = 'D:\projects\science\drosophila-brain-model\Connectivity_783.http.parquet'
$src = 'D:\projects\science\drosophila-brain-model\Connectivity_783.parquet'
$expected = 100804642

Add-Type -AssemblyName System.Net.Http
$handler = New-Object System.Net.Http.HttpClientHandler
$handler.AllowAutoRedirect = $true
$client = New-Object System.Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromMinutes(30)
$client.DefaultRequestHeaders.UserAgent.ParseAdd('dsh')

for ($attempt = 1; $attempt -le 60; $attempt++) {
    $have = 0
    if (Test-Path $dst) { $have = (Get-Item $dst).Length }
    if ($have -ge $expected) { break }

    try {
        $req = New-Object System.Net.Http.HttpRequestMessage('GET', $url)
        if ($have -gt 0) {
            $req.Headers.Range = New-Object System.Net.Http.Headers.RangeHeaderValue($have, $null)
        }
        $resp = $client.SendAsync($req, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).Result
        $status = [int]$resp.StatusCode
        $stream = $resp.Content.ReadAsStreamAsync().Result
        $fs = [System.IO.File]::Open($dst, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        if ($status -eq 200) { $fs.SetLength(0) }
        $fs.Seek(0, [System.IO.SeekOrigin]::End) | Out-Null
        $buf = New-Object 'byte[]' 1048576
        $total = 0
        while (($n = $stream.Read($buf, 0, $buf.Length)) -gt 0) {
            $fs.Write($buf, 0, $n)
            $total += $n
        }
        $fs.Close(); $stream.Close(); $resp.Dispose()
        $now = (Get-Item $dst).Length
        Write-Output ("attempt {0}: status {1}, +{2:N1} MB -> {3:N1} MB" -f $attempt, $status, ($total / 1MB), ($now / 1MB))
    } catch {
        Write-Output ("attempt {0}: error {1}" -f $attempt, $_.Exception.Message)
        Start-Sleep -Seconds 3
    }
}

if (Test-Path $dst) {
    $len = (Get-Item $dst).Length
    Write-Output ("FINAL http copy: {0} bytes (expected {1})" -f $len, $expected)
    if ($len -eq $expected) {
        $a = (Get-FileHash $src -Algorithm SHA256).Hash
        $b = (Get-FileHash $dst -Algorithm SHA256).Hash
        Write-Output ("curl sha256: {0}" -f $a)
        Write-Output ("http sha256: {0}" -f $b)
        Write-Output ("identical: {0}" -f ($a -eq $b))
    }
}
