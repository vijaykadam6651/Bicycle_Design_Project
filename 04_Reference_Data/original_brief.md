# Road Bicycle Design Project (SolidWorks)
**Project Location:** `E:\Bicycle_Design_Project`  
**Target Architecture:** High-Performance 700c Road Bike Layout  

---

## 1. Automated Workspace Initialization

To instantly establish the project layout on your local environment, open your Windows **Command Prompt (as Administrator)** and execute the following unified command sequence:

```cmd
mkdir "E:\Bicycle_Design_Project" && cd /d "E:\Bicycle_Design_Project" && mkdir "01_Parts" "02_Assemblies" "03_Drawings" "04_Reference_Data" "05_Purchased_Components" && echo # Road Bicycle Design Project > README.md
```

### Directory Architecture Reference
*   📁 **`01_Parts/`** : Custom-modeled proprietary parts (Frame skeleton, custom lugs, dropouts).
*   📁 **`02_Assemblies/`** : Mechanical sub-assemblies (Front fork array, rear gear cluster, main frame).
*   📁 **`03_Drawings/`** : Production blueprints, geometric dimensioning and tolerancing (GD&T) sheets.
*   📁 **`04_Reference_Data/`** : Ergonomic data tables, target structural specifications, aero-profile vectors.
*   📁 **`05_Purchased_Components/`** : Third-party supplier files (Shimano/SRAM group sets, 700c tires, saddle).

---

## 2. Core Geometric Target Parameters (700c Road Spec)

When constructing the initial parameter space in your master skeleton part (`Road_Frame_Skeleton.sldprt`), adhere strictly to these aggressive performance road bike baselines:

| Design Dimension | Standard Value | Engineering Purpose / Intent |
| :--- | :--- | :--- |
| **Wheelbase** | `980mm - 1000mm` | Ensures a hyper-responsive, sharp cornering profile |
| **Head Tube Angle** | `73.0°` | Steep angle; provides direct, immediate steering feedback |
| **Seat Tube Angle** | `73.5°` | Optimizes biomechanical hip power transfer to the bottom bracket |
| **Bottom Bracket Drop** | `70mm` | Lowers center of gravity beneath axle centerlines for stability |
| **Chainstay Length** | `405mm - 415mm` | Minimizes rear-triangle flex, maximizing drivetrain acceleration |
| **Wheel Outer Diameter** | `~680mm` | True physical clearance envelope matching standard 700x25c tires |

---

## 3. Engineering Workflow Execution Steps

### Phase 1: The Master Skeleton Component
1. Create a new part and save it immediately as `E:\Bicycle_Design_Project\01_Parts\Road_Frame_Skeleton.sldprt`.
2. Construct a layout sketch on the **Right Plane**.
3. Map out the main triangle and rear stays using construction geometry lines driven precisely by the angles outlined in Section 2.
4. Establish reference points at the Front Dropouts, Rear Dropouts, and the Bottom Bracket center.

### Phase 2: Structural Frame Generation
Select one of the following two manufacturing pipelines to flesh out the master skeleton geometry:
*   **Aerodynamic Carbon Fiber / Hydroformed Aluminum:** Generate planes normal to your layout sketch lines. Create aerodynamic cross-sections, and execute a **Loft** or **Sweep** across the frame geometry. Use **Shell** features to dictate wall thickness constraints.
*   **Welded Metal Construction (Chromoly / Titanium / Round Alloy):** Navigate to the **Weldments** tab. Assign structural member profiles (e.g., ISO Pipe or specialized oval profiles) to your construction lines. Utilize the **Trim/Extend** command to cut perfectly coped joints.

### Phase 3: Assembly Integration and Mating Constraints
1. Initialize a main workspace assembly: `E:\Bicycle_Design_Project\02_Assemblies\Bicycle_Main_Assembly.sldasm`.
2. Insert your fabricated structural frame component as the foundational asset. Right-click and choose **Fix** to ground its origin.
3. Import sub-assemblies (e.g., Fork and Cockpit layout).
4. Apply geometric mates:
    *   **Concentric Mates** for steering columns, bottom bracket axles, and hub assemblies.
    *   **Distance/Width Mates** to align hub widths perfectly across front and rear dropout drop zones.
    *   **Mechanical Gear Mates** linking crank rotations to rear cassette updates for motion checking.

### Phase 4: Validation & Quality Control
*   **Interference Detection:** Run under the *Evaluate* tab to check for overlapping geometries between the pedal paths, chainring teeth, frame clearance envelopes, and front tire swing paths.
*   **Clearance Analysis:** Ensure a minimum of **4mm to 6mm** structural gap remains between the inflated rear tire boundary and the inner chainstay walls to account for real-world wheel flexing.

---

## 4. SolidWorks Revision Control Protocol (Git Setup)

Because SolidWorks objects are binary files (`.sldprt`, `.sldasm`), traditional code diff engines cannot parse them. To prevent directory corruption and bloat, place the following configuration file in your root workspace folder.

### Project `.gitignore` File Configuration
Save this block exactly as `.gitignore` in `E:\Bicycle_Design_Project\` to manage your local tracking layer cleanly:

```gitconfig
# Ignore SolidWorks Lock and Temporary Files
~\$*
*.swp
*.bak
*.err
*.log

# Ignore Automatic Master Cam / NC Post Toolpaths
*.nc
*.gcode

# Ignore Local OS Metadata and IDE Workspace files
.DS_Store
Thumbs.db
.vs/
.idea/

# Large Files Tracking Reminder
# Ensure Git LFS is tracking binary assets to prevent repository bloat:
# git lfs track "*.sldprt"
# git lfs track "*.sldasm"
# git lfs track "*.slddrw"
```
