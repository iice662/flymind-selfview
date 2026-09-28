# Generate placeholder sprites for FlyMind with System.Drawing.
# Real art can replace these later; the sizes/format match what the mod expects:
#   NPCs/Fly.png        4 frames of 12x12 (idle, walk, walk, feed)
#   Items/FlyFood.png   20x20 item sprite
Add-Type -AssemblyName System.Drawing

$root = 'D:\projects\science\terraria-fly-mod'
$npcDir = Join-Path $root 'NPCs'
$itemDir = Join-Path $root 'Items'
New-Item -ItemType Directory -Force $npcDir, $itemDir | Out-Null

function C([int]$a, [int]$r, [int]$g, [int]$b) {
    return [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
}

function Brush([System.Drawing.Color]$c) {
    return New-Object System.Drawing.SolidBrush $c
}

function PenOf([System.Drawing.Color]$c, [int]$w) {
    return New-Object System.Drawing.Pen $c, $w
}

# ---------------------------------------------------------------- fly spritesheet
$fw = 12; $fh = 12; $frames = 4
$bmp = New-Object System.Drawing.Bitmap ($fw * $frames), $fh, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.Clear([System.Drawing.Color]::Transparent)
$gfx.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None

$body = C 255 45 38 30
$thorax = C 255 70 58 44
$wing = C 170 210 220 235
$wingHi = C 220 235 245 255
$eye = C 255 150 40 30
$leg = PenOf (C 255 30 24 20) 1
$brushBody = Brush $body
$brushThorax = Brush $thorax
$brushWing = Brush $wing
$brushWingHi = Brush $wingHi
$brushEye = Brush $eye

for ($f = 0; $f -lt $frames; $f++) {
    $ox = $f * $fw
    # abdomen / thorax / head
    $gfx.FillEllipse($brushBody, ($ox + 2), 4, 6, 5)
    $gfx.FillEllipse($brushThorax, ($ox + 6), 4, 4, 4)
    $gfx.FillEllipse($brushEye, ($ox + 9), 5, 2, 2)
    # wings: raised when walking, folded when idle, spread when feeding
    if ($f -eq 0) {
        $gfx.FillEllipse($brushWing, ($ox + 3), 2, 5, 3)
    }
    elseif ($f -eq 3) {
        $gfx.FillEllipse($brushWingHi, ($ox + 2), 1, 7, 4)
        $gfx.FillEllipse($brushWing, ($ox + 1), 6, 6, 3)
    }
    else {
        $gfx.FillEllipse($brushWing, ($ox + 4), 2 + (($f % 2) * 1), 5, 4)
    }
    # legs
    $gfx.DrawLine($leg, ($ox + 5), 8, ($ox + 3), 11)
    $gfx.DrawLine($leg, ($ox + 7), 8, ($ox + 7), 11)
    $gfx.DrawLine($leg, ($ox + 9), 7, ($ox + 11), 10)
    # proboscis when feeding
    if ($f -eq 3) {
        $gfx.DrawLine($leg, ($ox + 10), 6, ($ox + 11), 8)
    }
}
$gfx.Dispose()
$bmp.Save((Join-Path $npcDir 'Fly.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output ('wrote NPCs\Fly.png  ' + ((Get-Item (Join-Path $npcDir 'Fly.png')).Length) + ' bytes')

# ---------------------------------------------------------------- food item sprite
$b2 = New-Object System.Drawing.Bitmap 20, 20, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g2 = [System.Drawing.Graphics]::FromImage($b2)
$g2.Clear([System.Drawing.Color]::Transparent)
$g2.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

# a lump of over-ripe fruit with a few flies' worth of appeal
$g2.FillEllipse((Brush (C 255 140 74 42)), 2, 6, 16, 12)
$g2.FillEllipse((Brush (C 255 176 108 62)), 4, 4, 12, 10)
$g2.FillEllipse((Brush (C 255 205 150 90)), 6, 5, 6, 5)
$g2.FillEllipse((Brush (C 200 90 40 30)), 12, 12, 3, 2)
$g2.FillEllipse((Brush (C 200 70 110 45)), 5, 13, 4, 2)
# a small green leaf, so it reads as "food" in the hotbar
$g2.FillEllipse((Brush (C 255 96 152 66)), 11, 1, 7, 4)
$g2.DrawLine((PenOf (C 255 60 110 50) 1), 12, 4, 8, 8)
$g2.Dispose()
$b2.Save((Join-Path $itemDir 'FlyFood.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$b2.Dispose()
Write-Output ('wrote Items\FlyFood.png  ' + ((Get-Item (Join-Path $itemDir 'FlyFood.png')).Length) + ' bytes')
