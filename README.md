# Road Bicycle Design Project

Revision A | 7 November 2026 | **Concept design - not for manufacture**

This package develops the supplied 700c road-bike brief into a parameterized welded round-tube concept, exchange CAD assembly, dimensioned concept drawings and a documented path into SolidWorks. The original brief is preserved in `04_Reference_Data/original_brief.md`.

## Start here

- `03_Drawings/Road_Bicycle_Design_Project.pdf`: illustrated project report and dimensioned drawings.
- `03_Drawings/Bicycle_Concept_Preview.png`: rendering derived directly from the CAD assembly.
- `02_Assemblies/Bicycle_Main_Assembly.step`: complete static concept assembly; import with millimetre units.
- `01_Parts/Road_Frame.step`: hollow tube frame concept with nominal coped main-tube joints.
- `01_Parts/Road_Frame_Skeleton.dxf`: side-view construction layout, DXF XY = project XZ.
- `01_Parts/Road_Frame_Skeleton.step`: three-dimensional construction edges.
- `06_Automation/SOLIDWORKS_BUILD.md`: native conversion instructions and remaining feature/mate work.
- `04_Reference_Data/validation_results.json`: model checks, STEP round-trip results and open validation items.

## Design choices

The brief allows a welded-metal pipeline. This package selects round steel tubes as a modelling assumption; alloy, butting, welding procedure and structural sizing remain unselected. The nominal medium-size layout uses a 520 mm seat tube, 140 mm head tube, 45 mm fork offset, 370 mm axle-to-crown dimension and 12 mm lower headset stack. These additions close the geometry; they are not rider-fit or supplier approvals.

| Brief requirement | Selected geometry |
|---|---:|
| Wheelbase 980-1000 mm | 990 mm |
| Head angle | 73.0 deg |
| Seat angle | 73.5 deg |
| BB drop | 70 mm |
| Chainstay centre distance 405-415 mm | 410 mm |
| Wheel outer envelope | 680 mm |
| Nominal tire width | 25 mm |

Project coordinates are X forward, Y left, Z up, with BB at (0,0,0). Drive components are on negative Y. All model dimensions are millimetres. The chainstay requirement is the direct BB-to-rear-axle distance; the segmented stay path is longer. The down tube joins the head tube 35 mm above its lower end to resolve the initial front-tire conflict.

The 680 x 25 mm toroidal tire is a **clearance envelope**, not an exact 700x25C supplier tire. 25-622 specifies nominal width and bead-seat diameter; actual inflated shape depends on the selected tire/rim. The assumed 100/130 mm hub spacing and rim-brake arrangement must be replaced with a compatible component specification. No brake calipers, levers, cables, shifters, derailleur or functional chain links are modeled.

## Delivered versus pending

**Generated and checked:** STEP solids, static assembly, 2D/3D skeleton exchange geometry, nominal surface clearances, discrete steering samples, conservative crank-arm swept volumes, STEP re-import checks, parameter/coordinate/tube tables, reference-component register, report and scripts.

**Not generated here:** `.sldprt`, `.sldasm` or `.slddrw` native files. SolidWorks is not installed on this computer. The supplied COM build script is syntax-reviewed but has not run against SolidWorks. It is intended to create a fixed construction skeleton and native imported parts/static assembly after installation. It does not create an editable weldment feature tree, dimensional equations, functional mating, or production drawings automatically.

**Engineering still required:** supplier interface definition, detailed dropout and axle retention design, bearing seats and threads, bend radii and weld detail, brakes and routing, tolerance stack-up, actual tire/chain/pedal/toe clearance, continuous motion, rider fit and structural validation. Stay segments and several reference components remain separate/intersecting bodies representing a concept; their apparent connections are not qualified joints. Do not treat displayed tube wall sizes or drawing reference dimensions as a manufacturing specification.

## Regenerate the exchange project

The local `.venv` contains the CAD generator environment. From this project folder:

```powershell
.\.venv\Scripts\python.exe .\06_Automation\prepare_parameters.py
.\.venv\Scripts\python.exe .\06_Automation\build_cad.py
.\.venv\Scripts\python.exe .\06_Automation\create_report.py
```

Edit `prepare_parameters.py` for a new design iteration, then regenerate all outputs. `design_parameters.json` is its generated single source used by CAD/report/native-build scripts. Reference/clearance tables and drawings must be regenerated together. A different computer needs Python 3.12 and the dependencies in `06_Automation/requirements.txt`; the local environment itself is excluded from the delivery archive.

## SolidWorks workflow

Open the STEP assembly to review the concept immediately. For native conversion, follow `06_Automation/SOLIDWORKS_BUILD.md` with installed SolidWorks and valid part/assembly templates. The script refuses existing output files by default. Its skeleton is a Right Plane construction sketch in a separate part with documented axis mapping; exchange CAD keeps project XYZ.

Rebuild intended proprietary parts with native structural members and Trim/Extend, then replace grounded reference components with validated supplier files. Apply steering, hub and crank concentric mates and axial/width constraints. Use an illustrative 50:17 mechanical gear relation only after verifying rotation directions and wheel/freehub behavior; it is not a chain simulation. Run Evaluate > Interference Detection, Clearance Verification and motion sweeps with the actual components. Complete the checklist before issuing native production drawings.

## Revision control

A local Git repository and local Git LFS hooks are initialized. `.gitignore` includes the brief's block plus generator exclusions. `.gitattributes` tracks native SolidWorks, STEP, PNG and PDF assets through LFS. No commit or remote upload has been made. Use `git status` to review, then commit when ready. Keep parameter sources, CAD and drawings in the same revision; record supplier part revisions and attach validation evidence for later releases.

See `04_Reference_Data/requirements_traceability.md` for every brief instruction and its delivery status, and `04_Reference_Data/sources.md` for technical references.
"# Bicycle_Design_Project" 
