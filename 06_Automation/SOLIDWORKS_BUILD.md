# Native SOLIDWORKS build and completion guide

Revision A · 7 November 2026 · **Prepared, not executed in SOLIDWORKS**

SOLIDWORKS desktop was unavailable on the preparation machine. The delivered STEP geometry, DXF layout and drawings are interchange/concept deliverables. No `.sldprt`, `.sldasm` or `.slddrw` file is claimed as delivered or verified. The PowerShell script provides the next native conversion step; its COM behavior must be verified on a licensed installation.

## Run the script

Use a licensed Windows SOLIDWORKS desktop installation with STEP import available. Save your current work before running. Use a clean part template containing only the three standard reference planes, in Front/Top/Right order, and a standard assembly template. The script reads the configured default templates, or accepts explicit paths. Administrator privileges are not required.

First, check source paths and coordinate consistency without opening SOLIDWORKS:

```powershell
powershell.exe -NoProfile -STA -File "E:\Bicycle_Design_Project\06_Automation\Build-SolidWorksProject.ps1" -CheckInputs
```

Then run in 64-bit Windows PowerShell 5.1:

```powershell
powershell.exe -NoProfile -STA -File "E:\Bicycle_Design_Project\06_Automation\Build-SolidWorksProject.ps1"
```

If defaults are missing, use your actual installed template paths:

```powershell
& 'E:\Bicycle_Design_Project\06_Automation\Build-SolidWorksProject.ps1' `
  -PartTemplate 'C:\Your Templates\Part.prtdot' `
  -AssemblyTemplate 'C:\Your Templates\Assembly.asmdot'
```

If your organization's execution policy prevents scripts, use its approved signing or execution process. The script deliberately does not alter execution policy or SOLIDWORKS global import settings. STEP importer or 3D Interconnect settings may require adjustment in SOLIDWORKS. An individual STEP must open as a solid part, possibly multibody. A file imported as an assembly, empty geometry, a missing template, or a failed save stops the process with an error.

Keep the source STEP files with the project. Depending on 3D Interconnect settings, the native imported part can retain an external reference to its STEP source. Inspect these references in SOLIDWORKS and decide whether to retain or break them under your revision-control process before transferring or releasing native files.

Existing native output files are never overwritten. For another revision, make a separate copy of the source package and provide `-ProjectRoot` pointing to it. A failure can leave successfully saved earlier outputs and open unsaved documents; inspect the JSON run report, preserve useful work and restart in a clean revision copy. The script does not delete files, close other documents or terminate SOLIDWORKS.

## What the automation creates

| Output | Construction | Completion status after a successful run |
| --- | --- | --- |
| `01_Parts/Road_Frame_Skeleton.sldprt` | Native sketch on the third standard reference plane, verified to be the YZ Right Plane | Exact source coordinates; construction members, wheel envelopes and BB/front/rear reference points; fixed geometry, not an equation-driven design tree |
| Component `.sldprt` files listed in `04_Reference_Data/component_manifest.json` | STEP import and native save | Imported solid geometry; no reconstructed weldment, loft, sweep or shell feature history |
| `02_Assemblies/Bicycle_Main_Assembly.sldasm` | Separate native components inserted at the common source origin | Every component fixed in the illustrated position; no geometric or mechanical mates |
| `06_Automation/solidworks-run-*.json` | Execution report | Actual file saves, error/warning codes, sketch orientation, body counts and component transforms |

The script checks its inputs before contacting COM, and checks import document type, solid-body presence, save results, component count, identity placement and fixed state during execution. These are automation checks, not structural or functional acceptance tests.

## Coordinate convention and editability

All STEP files use the common project axes **X forward, Y left, Z up**, in millimetres, with the origin at the bottom bracket. Component geometry is already in its assembled position. The script explicitly applies an identity component transform after insertion because insertion position arguments alone do not establish a precise common origin. It fixes the frame and every placeholder component to preserve the static concept.

The separate native master sketch follows the brief's **Right Plane** requirement. Its local sketch x is project X; its local sketch y is project Z. The lateral project Y coordinate is projected out. The standard SOLIDWORKS Right Plane is global YZ, so this native skeleton has a different orientation from the STEP coordinate frame. The actual sketch basis is recorded in the run report; no unverified rotation is silently applied. The skeleton is not inserted into the assembly. To drive a native frame from it, use the skeleton coordinate system consistently, then establish and verify an explicit transform when replacing the STEP frame.

Left/right stays share one side projection, so the duplicate right-side lines are omitted. Their true 3D lateral offsets remain in `design_parameters.json` and STEP geometry. The chainstay baseline is the BB-to-rear-axle reference length; bent physical tube segments have different developed lengths. The down tube joins the head tube above its lower endpoint, as specified by `DownTubeHead` in the source data.

Fixed sketch relations preserve the supplied angles and coordinates. They are native editable entities, but they are **not** a fully dimension/equation-driven parametric model. To change the source layout, update the source parameters, regenerate the neutral package with its provided generator, then run in a fresh revision copy. To develop it directly in SOLIDWORKS, remove the relevant Fixed relations, add coincident and dimensional relationships, and verify the results against the parameter table. Do not treat unconstrained edits as automatically preserving the target geometry.

## Complete the requested native modeling workflow

1. Open the native skeleton and measure the wheelbase, 73.0° head angle, 73.5° seat angle, 70 mm BB drop, 410 mm BB-to-rear-axle length and 680 mm wheel envelope. Confirm the plane and orientation. Replace Fixed relations with named driving dimensions/equations and shared-point relations if a native parametric skeleton is required.
2. For the chosen welded round-tube concept, create a native 3D layout for the lateral stays from the parameter coordinates. Assign the agreed tube profiles with **Weldments → Structural Member**. Use **Trim/Extend** and detailed joint features to cope intersections. The STEP model's tube intersections do not supply manufacturing joint design. Finalize material grade, wall selection, end treatments, bearing seats, dropout attachment, brake mounting and weld specification with engineering review.
3. Keep the frame fixed. Float the fork and apply a concentric steering-axis mate plus an axial location mate; retain the intended steering degree of freedom. Float each wheel, mate its hub concentrically with the corresponding axle and center it using width or symmetric distance mates. Define compatible hardware and supplier dimensions before constraining real components.
4. Float the crankset and mate its spindle concentrically with the BB axis, with the correct axial location. Replace envelope geometry with actual components where bearing and axle detail is needed. The supplied placeholders do not represent complete bearing assemblies.
5. Add a mechanical gear relation only for a declared drivetrain configuration. The illustrative 50/17 tooth ratio implies rear-sprocket speed `50/17` times crank speed while engaged. Check the solver's rotation direction: a bicycle chain connects parallel axes with the same rotation sense, whereas an external-gear analogy may reverse it. A gear mate does not model chain articulation, shifting, slack, derailleur capacity or the freewheel. Use a suppressed/alternative configuration for coasting; never claim a continuous gear mate reproduces freewheel behavior.
6. Create native `.slddrw` documents from the finished native parts/assembly using your approved drawing template. The package's concept drawings are not released production blueprints. Establish functional datum schemes and manufacturing tolerances after the hardware and process are selected.

## SOLIDWORKS validation record to complete

Record the SOLIDWORKS version, configuration, model revision, enabled components and result evidence for each check below. These checks are **pending** until performed on the native model.

| Check | Procedure and acceptance evidence |
| --- | --- |
| Imported solids | Run Import Diagnostics on each part; resolve faulty faces/gaps; record solid body counts and scale. Confirm all common origins and orientations. |
| Static interference | Evaluate → Interference Detection. Include tire envelopes, crank/pedals, frame, fork and drivetrain. Categorize intended tube-joint overlaps separately from unintended collisions; do not accept all overlaps automatically. |
| Rear tire clearance | Measure inflated rear-tire-to-chainstay and seatstay distances on both sides, including bends and junctions. Use 6 mm nominal project target and verify tolerance/deflection allowance; the requested 4–6 mm gap is not a guarantee for an actual wheel/tire combination. |
| Steering sweep | Release the steering degree of freedom and sweep both directions through the declared range. Evaluate tire/fork/frame, cable/hose and toe/pedal envelopes throughout the sweep, not just at endpoints. |
| Pedal/crank rotation | Sweep a complete crank revolution with representative pedals and footwear, checking chainstay, tire and frame clearance. Verify ground clearance for intended lean and suspension/tire conditions. |
| Drivetrain motion | Select the declared tooth combination, verify speed ratio and rotation direction, and separately check coasting and shifting behavior with an appropriate mechanism model. |
| Structural suitability | Establish rider/load envelope, material and joint allowables, load cases and applicable bicycle test requirements; perform calculations, simulation and physical validation before a manufacturing release. |

## API references used in preparation

These primary SOLIDWORKS references informed the script; consulting documentation is not evidence that the script ran successfully.

- [GetDocumentTemplate](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.isldworks~getdocumenttemplate.html): configured template lookup.
- [STEP import data](https://help.solidworks.com/2024/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IImportStepData.html) and [LoadFile4](https://help.solidworks.com/2015/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~LoadFile4.html): import settings and foreign-file loading.
- [CreatePoint](https://help.solidworks.com/2021/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchManager~CreatePoint.html) and [ModelToSketchTransform](https://help.solidworks.com/2022/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketch~ModelToSketchTransform.html): native sketch creation and orientation inspection.
- [Component configuration options](https://help.solidworks.com/2025/english/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swAddComponentConfigOptions_e.html), [Transform2](https://help.solidworks.com/2015/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.icomponent2~transform2.html) and [FixComponent](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.iassemblydoc~fixcomponent.html): static component insertion and placement.
- [SaveAs](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDocExtension~SaveAs.html): native save result and warning checks. The established API is used for compatibility; newer releases also expose newer SaveAs variants.
