#requires -Version 5.1
<#
.SYNOPSIS
Creates a native coordinate-driven Right Plane skeleton and a static native
assembly from this project's STEP components, using installed SOLIDWORKS COM.
.DESCRIPTION
Prepared but NOT executed against SOLIDWORKS. Run in 64-bit Windows PowerShell
5.1 with -STA. This script does not create weldment history, mates, drawings,
strength validation, or manufacturing-ready geometry. See SOLIDWORKS_BUILD.md.
Existing native outputs are never overwritten. Use a separate project copy
for a new revision. -CheckInputs performs a read-only check without COM.
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = 'E:\Bicycle_Design_Project',
    [string]$PartTemplate = '',
    [string]$AssemblyTemplate = '',
    [switch]$CheckInputs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectFull = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\')
$projectPrefix = $projectFull + '\'

function Resolve-ProjectPath([string]$RelativePath) {
    if ([IO.Path]::IsPathRooted($RelativePath)) {
        throw "Manifest paths must be relative to the project: $RelativePath"
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $projectFull $RelativePath))
    if (-not $candidate.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path leaves the project directory: $RelativePath"
    }
    return $candidate
}

function Assert-Input([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Get-Point([string]$Name) {
    $property = $design.points.PSObject.Properties[$Name]
    Assert-Input ($null -ne $property) "Missing point '$Name' in design_parameters.json."
    [double[]]$values = $property.Value
    Assert-Input ($values.Count -eq 3) "Point '$Name' must have three coordinates."
    foreach ($value in $values) {
        Assert-Input (-not [double]::IsNaN($value) -and -not [double]::IsInfinity($value)) "Non-finite point '$Name'."
    }
    return ,$values
}

function Assert-Near([double]$Actual, [double]$Expected, [string]$Name) {
    Assert-Input ([Math]::Abs($Actual - $Expected) -lt 0.00001) "$Name does not match the parameter/point data: $Actual versus $Expected. Regenerate the source package first."
}

$parameterPath = Resolve-ProjectPath '04_Reference_Data\design_parameters.json'
$manifestPath = Resolve-ProjectPath '04_Reference_Data\component_manifest.json'
$design = Get-Content -Raw -LiteralPath $parameterPath | ConvertFrom-Json
# Windows PowerShell 5.1 writes a JSON array as one pipeline object, while newer
# PowerShell versions enumerate it. Normalize after assignment, not around the
# ConvertFrom-Json pipeline, to avoid a nested one-element array on 5.1.
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$manifest = @($manifest)
Assert-Input ($design.units -eq 'mm') 'Only millimetre parameter input is supported.'
Assert-Input ($manifest.Count -gt 0) 'The component manifest is empty.'
Assert-Input ($manifest[0].name -eq 'Road_Frame') 'The first manifest entry must be Road_Frame.'

$bb = Get-Point 'BB'
$rear = Get-Point 'RearAxle'
$front = Get-Point 'FrontAxle'
$seat = Get-Point 'SeatTop'
$hl = Get-Point 'HeadLower'
$hu = Get-Point 'HeadUpper'
Assert-Near ($front[0] - $rear[0]) $design.parameters.wheelbase_mm 'Wheelbase'
Assert-Near ($rear[2] - $bb[2]) $design.parameters.bb_drop_mm 'BB drop'
Assert-Near ($front[2] - $rear[2]) 0 'Axle level'
Assert-Near ([Math]::Sqrt([Math]::Pow($rear[0]-$bb[0],2)+[Math]::Pow($rear[2]-$bb[2],2))) $design.parameters.chainstay_mm 'Chainstay reference length'
Assert-Near ([Math]::Atan2($hu[2]-$hl[2],$hl[0]-$hu[0])*180/[Math]::PI) $design.parameters.head_angle_deg 'Head angle'
Assert-Near ([Math]::Atan2($seat[2]-$bb[2],$bb[0]-$seat[0])*180/[Math]::PI) $design.parameters.seat_angle_deg 'Seat angle'

$skeletonPath = Resolve-ProjectPath '01_Parts\Road_Frame_Skeleton.sldprt'
$assemblyPath = Resolve-ProjectPath '02_Assemblies\Bicycle_Main_Assembly.sldasm'
$nativePaths = @($skeletonPath, $assemblyPath)
foreach ($entry in $manifest) {
    $source = Resolve-ProjectPath $entry.step_path
    $destination = Resolve-ProjectPath $entry.native_path
    Assert-Input (Test-Path -LiteralPath $source -PathType Leaf) "Missing STEP: $source"
    Assert-Input ([IO.Path]::GetExtension($source) -match '^\.st(e)?p$') "Not a STEP path: $source"
    Assert-Input ([IO.Path]::GetExtension($destination) -ieq '.sldprt') "Not a native part path: $destination"
    $nativePaths += $destination
}
Assert-Input (@($nativePaths | Select-Object -Unique).Count -eq $nativePaths.Count) 'Duplicate native output paths.'
foreach ($path in $nativePaths) {
    Assert-Input (-not (Test-Path -LiteralPath $path)) "Refusing to overwrite existing native file: $path. Use a new revision copy."
}
if ($CheckInputs) {
    Write-Output "Input checks passed: $($manifest.Count) STEP components; geometry and output paths consistent. SOLIDWORKS was not contacted."
    return
}

Assert-Input ([Environment]::Is64BitProcess) 'Use 64-bit Windows PowerShell.'
Assert-Input ($PSVersionTable.PSEdition -eq 'Desktop') 'Use Windows PowerShell 5.1, not PowerShell 7.'
Assert-Input ([Threading.Thread]::CurrentThread.ApartmentState -eq 'STA') 'Start powershell.exe with -STA.'

$report = [ordered]@{
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    status = 'started'
    source_revision = $design.revision
    limitations = @('Concept geometry only', 'No mechanical mates', 'No native weldment/loft history', 'No SolidWorks clearance or interference validation', 'No manufacturing release')
    skeleton = $null
    components = @()
    saved_files = @()
    error = $null
}
$runStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$reportPath = Resolve-ProjectPath ("06_Automation\solidworks-run-$runStamp.json")
$script:sw = $null
$script:activeSketchManager = $null
$oldAddToDb = $false
$oldDisplay = $true

function Get-Template([int]$DocumentType, [string]$ExplicitPath) {
    $path = $ExplicitPath
    if ([string]::IsNullOrWhiteSpace($path)) {
        $path = $script:sw.GetDocumentTemplate($DocumentType, '', 0, 0.0, 0.0)
    }
    Assert-Input (-not [string]::IsNullOrWhiteSpace($path)) "SOLIDWORKS has no default template for document type $DocumentType. Supply -PartTemplate and -AssemblyTemplate."
    Assert-Input (Test-Path -LiteralPath $path -PathType Leaf) "Template does not exist: $path"
    return [IO.Path]::GetFullPath($path)
}

function Save-NewNative($Document, [string]$Path) {
    Assert-Input (-not (Test-Path -LiteralPath $Path)) "Refusing to overwrite $Path"
    $Document.ClearSelection2($true)
    [int]$saveError = 0
    [int]$saveWarning = 0
    # Current version=0; Silent=1. SaveAs remains supported across older releases.
    $saved = $Document.Extension.SaveAs($Path, 0, 1, $null, [ref]$saveError, [ref]$saveWarning)
    Assert-Input ($saved -and $saveError -eq 0 -and (Test-Path -LiteralPath $Path -PathType Leaf)) "Save failed ($saveError): $Path"
    if ($saveWarning -ne 0) { Write-Warning "Save warning code $saveWarning for $Path" }
    $report.saved_files += [ordered]@{ path = $Path; warning_code = $saveWarning }
}

function Get-ComDocumentType($Document) {
    # Avoid PowerShell resolving Object.GetType() instead of IModelDoc2.GetType().
    return [int]$Document.GetType().InvokeMember('GetType', [Reflection.BindingFlags]::InvokeMethod, $null, $Document, @())
}

function Fix-SketchEntity($Document, $Entity) {
    $Document.ClearSelection2($true)
    Assert-Input ($Entity.Select4($false, $null)) 'Could not select a sketch entity for its Fixed relation.'
    $Document.SketchAddConstraints('sgFIXED')
    $Document.ClearSelection2($true)
}

try {
    try { $script:sw = [Runtime.InteropServices.Marshal]::GetActiveObject('SldWorks.Application') }
    catch {
        try { $script:sw = New-Object -ComObject SldWorks.Application }
        catch { throw 'SOLIDWORKS desktop COM is unavailable. Install/activate SOLIDWORKS on this Windows machine, then rerun. No native CAD can be created here.' }
    }
    $script:sw.Visible = $true
    $partTemplatePath = Get-Template 1 $PartTemplate
    $assemblyTemplatePath = Get-Template 2 $AssemblyTemplate
    $report.solidworks_revision = $script:sw.RevisionNumber()

    $part = $script:sw.NewDocument($partTemplatePath, 0, 0.0, 0.0)
    Assert-Input ($null -ne $part) 'Could not create the skeleton part.'
    # Traverse feature types to avoid English/localized plane-name selection.
    $planes = @()
    $feature = $part.FirstFeature()
    while ($null -ne $feature) {
        if ($feature.GetTypeName2() -eq 'RefPlane') { $planes += $feature }
        $feature = $feature.GetNextFeature()
    }
    Assert-Input ($planes.Count -eq 3) 'Use a clean standard part template with exactly three default planes in Front, Top, Right order.'
    $rightPlane = $planes[2]
    Assert-Input ($rightPlane.Select2($false, 0)) 'Could not select the third reference plane.'
    $sketchManager = $part.SketchManager
    $script:activeSketchManager = $sketchManager
    $sketchManager.InsertSketch($true)
    $sketch = $sketchManager.ActiveSketch
    Assert-Input ($null -ne $sketch) 'Could not create a Right Plane sketch.'
    $math = $script:sw.GetMathUtility()
    $sketchToModel = $sketch.ModelToSketchTransform.Inverse()
    $origin = $math.CreatePoint([double[]]@(0,0,0)).MultiplyTransform($sketchToModel).ArrayData
    $xProbe = $math.CreatePoint([double[]]@(1,0,0)).MultiplyTransform($sketchToModel).ArrayData
    $yProbe = $math.CreatePoint([double[]]@(0,1,0)).MultiplyTransform($sketchToModel).ArrayData
    # A standard Right Plane is the global YZ plane. Verify, rather than relying
    # only on feature order. The plane's in-plane sign convention is recorded.
    Assert-Input ([Math]::Abs($origin[0])+[Math]::Abs($origin[1])+[Math]::Abs($origin[2]) -lt 1e-8) 'Template plane is offset from the model origin.'
    Assert-Input ([Math]::Abs($xProbe[0])+[Math]::Abs($yProbe[0]) -lt 1e-8) 'The third plane is not the expected global YZ Right Plane.'
    $oldAddToDb = $sketchManager.AddToDB
    $oldDisplay = $sketchManager.DisplayWhenAdded
    $sketchManager.AddToDB = $true
    $sketchManager.DisplayWhenAdded = $false

    # Side elevation: project (X,Y,Z) -> sketch (X,Z,0), millimetres -> metres.
    # Left/right stays project onto one another; omit duplicate R members.
    $segments = @()
    foreach ($member in $design.frame_members) {
        if ($member.name -match '(ChainstayR|SeatstayR)') { continue }
        $start = Get-Point $member.start
        $end = Get-Point $member.end
        $segment = $sketchManager.CreateLine($start[0]/1000, $start[2]/1000, 0.0, $end[0]/1000, $end[2]/1000, 0.0)
        Assert-Input ($null -ne $segment) "Could not create $($member.name)."
        $segment.ConstructionGeometry = $true
        $segments += $segment
    }
    foreach ($pair in @(@('RearAxle','FrontAxle'), @('BB','RearAxle'), @('HeadLower','FrontAxle'))) {
        $start = Get-Point $pair[0]
        $end = Get-Point $pair[1]
        $segment = $sketchManager.CreateLine($start[0]/1000, $start[2]/1000, 0.0, $end[0]/1000, $end[2]/1000, 0.0)
        Assert-Input ($null -ne $segment) 'Could not create a reference line.'
        $segment.ConstructionGeometry = $true
        $segments += $segment
    }
    foreach ($name in @('RearAxle', 'FrontAxle')) {
        $point = Get-Point $name
        $circle = $sketchManager.CreateCircleByRadius($point[0]/1000, $point[2]/1000, 0.0, $design.parameters.wheel_od_mm/2000)
        Assert-Input ($null -ne $circle) 'Could not create a wheel envelope.'
        $circle.ConstructionGeometry = $true
        $segments += $circle
    }
    $referencePoints = @()
    foreach ($name in @('BB','RearAxle','FrontAxle')) {
        $point = Get-Point $name
        $nativePoint = $sketchManager.CreatePoint($point[0]/1000, $point[2]/1000, 0.0)
        Assert-Input ($null -ne $nativePoint) "Could not create reference point $name."
        $referencePoints += $nativePoint
    }
    $sketchManager.AddToDB = $false
    $sketchManager.DisplayWhenAdded = $true
    foreach ($entity in ($segments + $referencePoints)) { Fix-SketchEntity $part $entity }
    $sketchFeature = $sketch.GetFeature()
    $sketchFeature.Name = 'Master_Layout_Right_Plane_Concept'
    $constraintStatus = $sketch.GetConstrainedStatus()
    $sketchManager.InsertSketch($true)
    $sketchManager.AddToDB = $oldAddToDb
    $sketchManager.DisplayWhenAdded = $oldDisplay
    $script:activeSketchManager = $null
    [void]$part.EditRebuild3()
    $part.ViewZoomtofit2()
    Save-NewNative $part $skeletonPath
    $report.skeleton = [ordered]@{
        path = $skeletonPath
        reference_plane = $rightPlane.Name
        native_sketch_constraint_status = $constraintStatus
        construction_segments = $segments.Count
        explicit_reference_points = $referencePoints.Count
        coordinate_mapping = 'Project X -> sketch x; project Z -> sketch y; lateral Y projected out. Separate orientation from imported STEP parts.'
        sketch_x_in_model = @($xProbe)
        sketch_y_in_model = @($yProbe)
        drive_method = 'Exact source coordinates with Fixed relations; edit source and regenerate, or replace Fixed relations with native dimensions.'
    }

    # Keep every imported native part loaded for AddComponent5.
    $loaded = @()
    foreach ($entry in $manifest) {
        $stepPath = Resolve-ProjectPath $entry.step_path
        $nativePath = Resolve-ProjectPath $entry.native_path
        $importData = $script:sw.GetImportFileData($stepPath)
        Assert-Input ($null -ne $importData) "STEP import data unavailable: $stepPath. Check STEP translator/3D Interconnect settings."
        $importData.MapConfigurationData = $false
        [int]$loadError = 0
        $imported = $script:sw.LoadFile4($stepPath, 'r', $importData, [ref]$loadError)
        Assert-Input ($null -ne $imported -and $loadError -eq 0) "STEP load failed ($loadError): $stepPath"
        Assert-Input ((Get-ComDocumentType $imported) -eq 1) "STEP opened as an assembly instead of a part: $stepPath. Import this individual file as a multibody part and retry in a clean revision folder."
        $bodies = @($imported.GetBodies2(0, $false)) # swSolidBody=0
        Assert-Input ($bodies.Count -gt 0 -and $null -ne $bodies[0]) "No solid bodies imported: $stepPath"
        Save-NewNative $imported $nativePath
        $loaded += [pscustomobject]@{ manifest = $entry; document = $imported; native_path = $nativePath; solid_body_count = $bodies.Count }
    }

    $assembly = $script:sw.NewDocument($assemblyTemplatePath, 0, 0.0, 0.0)
    Assert-Input ($null -ne $assembly) 'Could not create the native assembly.'
    # STEP components were exported already positioned in the common project
    # XYZ frame. Apply an explicit identity transform after insertion.
    [double[]]$identityData = @(1,0,0, 0,1,0, 0,0,1, 0,0,0, 1,0,0,0)
    $identity = $math.CreateTransform($identityData)
    foreach ($item in $loaded) {
        $beforeCount = @($assembly.GetComponents($true) | Where-Object { $null -ne $_ }).Count
        $component = $assembly.AddComponent5($item.native_path, 0, '', $false, '', 0.0, 0.0, 0.0)
        Assert-Input ($null -ne $component) "Component insertion failed: $($item.native_path)"
        $assembly.ClearSelection2($true)
        Assert-Input ($component.Select4($false, $null, $false)) 'Could not select inserted component.'
        $assembly.UnfixComponent()
        $component.Transform2 = $identity
        $actualTransform = $component.Transform2.ArrayData
        for ($index = 0; $index -le 12; $index++) {
            Assert-Input ([Math]::Abs($actualTransform[$index]-$identityData[$index]) -lt 1e-8) "Component identity placement failed: $($item.manifest.name)"
        }
        $assembly.FixComponent()
        Assert-Input ($component.IsFixed()) "Could not fix component: $($item.manifest.name)"
        $afterCount = @($assembly.GetComponents($true) | Where-Object { $null -ne $_ }).Count
        Assert-Input ($afterCount -eq $beforeCount+1) 'Assembly component count did not increase by one.'
        $report.components += [ordered]@{ name = $item.manifest.name; native_path = $item.native_path; solid_body_count = $item.solid_body_count; fixed = $true; transform = @($actualTransform) }
    }
    $assembly.ClearSelection2($true)
    [void]$assembly.EditRebuild3()
    $assembly.UpdateBox()
    $assembly.ViewZoomtofit2()
    Save-NewNative $assembly $assemblyPath
    $report.status = 'native_static_concept_created_pending_manual_review'
    Write-Output "Saved native skeleton, $($loaded.Count) imported parts, and static assembly. Mates and SolidWorks validation remain pending."
}
catch {
    $report.status = 'failed_partial_outputs_possible'
    $report.error = $_.Exception.Message
    throw
}
finally {
    if ($null -ne $script:activeSketchManager) {
        try {
            $script:activeSketchManager.AddToDB = $oldAddToDb
            $script:activeSketchManager.DisplayWhenAdded = $oldDisplay
        } catch { Write-Warning 'Could not restore sketch display settings.' }
    }
    # Leave documents visible for inspection. Never terminate the user's app.
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Output "Run report: $reportPath"
}
