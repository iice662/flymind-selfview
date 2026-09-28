# Dump real member signatures out of the game/tModLoader assemblies with Mono.Cecil,
# so the mod code can be written against the actual API instead of guessed names.
#
# Usage:
#     powershell -File dump_api.ps1 -TypeName "Terraria.Player" -Filter "QuickSpawnItem,GetSource"
param(
    [Parameter(Mandatory = $true)][string]$TypeName,
    [string]$Filter = ''
)

$cecil = 'D:\Steam\steamapps\common\tModLoader\Libraries\mono.cecil\0.11.6\lib\netstandard2.0\Mono.Cecil.dll'
Add-Type -Path $cecil

$assemblies = @(
    'D:\Steam\steamapps\common\tModLoader\tModLoader.dll',
    'D:\Steam\steamapps\common\tModLoader\Libraries\FNA\FNA.dll'
)
$resolver = New-Object Mono.Cecil.DefaultAssemblyResolver
$resolver.AddSearchDirectory('D:\Steam\steamapps\common\tModLoader')
$resolver.AddSearchDirectory('D:\Steam\steamapps\common\tModLoader\Libraries')
$rp = New-Object Mono.Cecil.ReaderParameters
$rp.AssemblyResolver = $resolver

$filters = @()
if ($Filter) { $filters = $Filter.Split(',') | ForEach-Object { $_.Trim() } }

foreach ($path in $assemblies) {
    if (-not (Test-Path $path)) { continue }
    $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path, $rp)
    $types = $asm.MainModule.Types
    $stack = New-Object System.Collections.Stack
    foreach ($t in $types) { $stack.Push($t) }
    while ($stack.Count -gt 0) {
        $t = $stack.Pop()
        if ($t.FullName -eq $TypeName -or $t.Name -eq $TypeName) {
            Write-Output ("=== {0}  (in {1})" -f $t.FullName, (Split-Path $path -Leaf))
            foreach ($f in $t.Fields) {
                if ($filters.Count -gt 0 -and -not ($filters | Where-Object { $f.Name -like "*$_*" })) { continue }
                Write-Output ("  FIELD  {0} {1}" -f $f.FieldType.Name, $f.Name)
            }
            foreach ($p in $t.Properties) {
                if ($filters.Count -gt 0 -and -not ($filters | Where-Object { $p.Name -like "*$_*" })) { continue }
                Write-Output ("  PROP   {0} {1}" -f $p.PropertyType.Name, $p.Name)
            }
            foreach ($m in $t.Methods) {
                if ($filters.Count -gt 0 -and -not ($filters | Where-Object { $m.Name -like "*$_*" })) { continue }
                if ($m.IsGetter -or $m.IsSetter) { continue }
                $ps = ($m.Parameters | ForEach-Object { "{0} {1}" -f $_.ParameterType.Name, $_.Name }) -join ', '
                Write-Output ("  METHOD {0} {1}({2})" -f $m.ReturnType.Name, $m.Name, $ps)
            }
            foreach ($n in $t.NestedTypes) { $stack.Push($n) }
        }
        else {
            foreach ($n in $t.NestedTypes) { $stack.Push($n) }
        }
    }
}
