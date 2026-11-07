"""Build exchange CAD and measure the nominal concept. Run prepare_parameters.py first.
No SolidWorks install is required. No part is a manufacturing release.
"""
from pathlib import Path
import json, math, csv
import cadquery as cq
import ezdxf

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'04_Reference_Data/design_parameters.json').read_text())
P=D['points']; V=cq.Vector
def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(a,k): return [x*k for x in a]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def cylinder(a,b,r):
    d=V(*b)-V(*a)
    return cq.Solid.makeCylinder(r,d.Length,V(*a),d.normalized())
def tube(a,b,od,wall):
    d=(V(*b)-V(*a)).normalized()
    return cylinder(a,b,od/2).cut(cylinder((V(*a)-d).toTuple(),(V(*b)+d).toTuple(),od/2-wall))
def compound(shapes): return cq.Compound.makeCompound(shapes)
def box_at(pos,dims): return cq.Workplane('XY').box(*dims).translate(tuple(pos)).val()
def ring(center,r_outer,r_inner,width):
    a=add(center,[0,-width/2,0]);b=add(center,[0,width/2,0])
    return tube(a,b,2*r_outer,r_outer-r_inner)
def tire(center): return cq.Solid.makeTorus(327.5,12.5,V(*center),V(0,1,0))

def main():
    shapes={}; display=[]; manifest=[]; members={}
    frame_color=(0.04,0.34,0.43); dark=(0.07,0.09,0.12); metal=(0.64,0.69,0.74)
    bb_outer=cylinder([0,-34,0],[0,34,0],20)
    head_outer=cylinder(P['HeadLower'],P['HeadUpper'],19)
    seat_outer=cylinder(P['BB'],P['SeatTop'],14.3)
    frame=[]
    for m in D['frame_members']:
        s=tube(P[m['start']],P[m['end']],m['od_mm'],m['wall_mm'])
        if m['name'] in ['SeatTube','DownTube'] or m['name'].startswith('Chainstay') and m['name'].endswith('1'): s=s.cut(bb_outer)
        if m['name'] in ['TopTube','DownTube']: s=s.cut(head_outer)
        if m['name']=='TopTube' or m['name'].startswith('Seatstay'): s=s.cut(seat_outer)
        members[m['name']]=s; frame.append(s)
    frame.append(tube([0,-34,0],[0,34,0],40,3))
    for sign in [-1,1]:
        c=add(P['RearAxle'],[0,sign*68,0])
        frame.append(ring(c,12,5,6))
    rear_axle_tool=cylinder(add(P['RearAxle'],[0,-90,0]),add(P['RearAxle'],[0,90,0]),5)
    frame=[s.cut(rear_axle_tool) for s in frame]
    shapes['Road_Frame']=compound(frame)
    u=D['steering_axis']; crown=P['ForkCrown']
    fork=[tube(crown,add(P['HeadUpper'],scale(u,55)),28.6,1.5),
          cylinder(P['ForkShoulderR'],P['ForkShoulderL'],15)]
    for side,sign in [('L',1),('R',-1)]:
        fork.append(tube(P[f'FrontDropout{side}'],P[f'ForkShoulder{side}'],25,1.5))
        fork.append(ring(add(P['FrontAxle'],[0,sign*53,0]),11,4.5,6))
    shapes['Front_Fork']=compound(fork)
    tire_shapes={}
    for name,axle,width in [('Front_Wheel',P['FrontAxle'],100),('Rear_Wheel',P['RearAxle'],130)]:
        t=tire(axle);tire_shapes[name]=t
        wheel=[t,ring(axle,315,286,20),cylinder(add(axle,[0,-width/2,0]),add(axle,[0,width/2,0]),12)]
        for side in [-1,1]:wheel.append(ring(add(axle,[0,side*30,0]),24,12,4))
        for i in range(20):
            a=2*math.pi*i/20;side=1 if i%2 else -1
            start=add(axle,[23*math.cos(a),30*side,23*math.sin(a)])
            end=add(axle,[286*math.cos(a+0.08*side),0,286*math.sin(a+0.08*side)])
            wheel.append(cylinder(start,end,1))
        shapes[name]=compound(wheel)
    stem_start=add(P['HeadUpper'],scale(u,40));bar=add(stem_start,[100,0,0])
    cockpit=[tube(stem_start,bar,32,2),tube(add(bar,[0,-210,0]),add(bar,[0,210,0]),24,2)]
    for side in [-1,1]:
        path=[add(bar,[0,side*210,0]),add(bar,[60,side*210,-20]),add(bar,[75,side*210,-80]),add(bar,[25,side*210,-125])]
        for a,b in zip(path,path[1:]): cockpit.append(tube(a,b,24,2))
    shapes['Cockpit']=compound(cockpit)
    sv=[-math.cos(math.radians(73.5)),0,math.sin(math.radians(73.5))]
    seatpost=tube(scale(sv,430),scale(sv,700),26.4,1.5)
    saddle_center=add(scale(sv,700),[15,0,12])
    saddle=cq.Workplane('XY',origin=tuple(saddle_center)).ellipse(130,68).extrude(16).val()
    shapes['Seatpost_Saddle']=compound([seatpost,saddle])
    ring_shape=ring([0,-45,0],105,85,4)
    crank=[ring_shape,cylinder([0,-75,0],[0,75,0],12)]
    for i in range(5):
        a=2*math.pi*i/5
        crank.append(cylinder([0,-45,0],[90*math.cos(a),-45,90*math.sin(a)],5))
    for side in [-1,1]:
        crank.append(cylinder([0,side*75,0],[0,side*75,side*172.5],9))
        crank.append(cylinder([0,side*75,side*172.5],[0,side*110,side*172.5],5))
        crank.append(box_at([0,side*110,side*172.5],[85,60,18]))
    shapes['Crankset']=compound(crank)
    shapes['Rear_Sprocket']=ring(add(P['RearAxle'],[0,-45,0]),35,15,4)
    # Two nominal chain strands, tangential to illustrative pitch circles, no links.
    delta=sub(P['RearAxle'],P['BB']);length=math.hypot(delta[0],delta[2]);e=[delta[0]/length,0,delta[2]/length]
    q=(101-34)/length;chains=[]
    for side in [-1,1]:
        norm=[q*e[0]+side*math.sqrt(1-q*q)*(-e[2]),0,q*e[2]+side*math.sqrt(1-q*q)*e[0]]
        a=add(scale(norm,101),[0,-45,0]);b=add(add(P['RearAxle'],scale(norm,34)),[0,-45,0])
        chains.append(cylinder(a,b,2))
    shapes['Chain_Path']=compound(chains)
    assembly=cq.Assembly(name='Bicycle_Main_Assembly')
    for name,s in shapes.items():
        folder='01_Parts' if name=='Road_Frame' else '02_Assemblies' if name=='Front_Fork' else '05_Purchased_Components'
        rel=f'{folder}/{name}.step'; cq.exporters.export(s,str(ROOT/rel))
        color=frame_color if name in ['Road_Frame','Front_Fork'] else dark if name in ['Cockpit','Seatpost_Saddle','Front_Wheel','Rear_Wheel'] else metal
        assembly.add(s,name=name,color=cq.Color(*color))
        display.append((name,s,color))
        manifest.append({'name':name,'step_path':rel,'native_path':f'{folder}/{name}.sldprt',
                         'role':'custom concept frame' if name=='Road_Frame' else 'concept reference envelope',
                         'solids':len(s.Solids()),'volume_mm3':s.Volume(),'valid':s.isValid()})
        print(f'Exported {name}: {len(s.Solids())} solids valid={s.isValid()}',flush=True)
    assembly.save(str(ROOT/'02_Assemblies/Bicycle_Main_Assembly.step'))
    (ROOT/'04_Reference_Data/component_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Skeleton exchange geometry preserves all three-dimensional reference lines.
    edges=[cq.Edge.makeLine(V(*P[m['start']]),V(*P[m['end']])) for m in D['frame_members']]
    cq.exporters.export(compound(edges),str(ROOT/'01_Parts/Road_Frame_Skeleton.step'))
    doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace()
    for layer,color in [('FRAME_CONSTRUCTION',4),('WHEEL_ENVELOPE',8),('REFERENCE_POINTS',1)]:doc.layers.new(layer,dxfattribs={'color':color})
    # XZ project side elevation maps to DXF XY. Duplicate side-projected stays omitted.
    seen=set()
    for m in D['frame_members']:
        a=P[m['start']];b=P[m['end']];key=tuple(round(v,5) for v in [a[0],a[2],b[0],b[2]])
        if key not in seen:ms.add_line((a[0],a[2]),(b[0],b[2]),dxfattribs={'layer':'FRAME_CONSTRUCTION'});seen.add(key)
    for k in ['RearAxle','FrontAxle']:ms.add_circle((P[k][0],P[k][2]),340,dxfattribs={'layer':'WHEEL_ENVELOPE'})
    for k in ['BB','RearAxle','FrontAxle','HeadLower','HeadUpper','SeatTop']:
        ms.add_point((P[k][0],P[k][2]),dxfattribs={'layer':'REFERENCE_POINTS'})
        ms.add_text(k,dxfattribs={'height':8,'insert':(P[k][0]+5,P[k][2]+5),'layer':'REFERENCE_POINTS'})
    doc.saveas(ROOT/'01_Parts/Road_Frame_Skeleton.dxf')
    # Exact OCCT boundary distances on the exported nominal geometry.
    checks=[]
    def gap(name,a,b,target,note=''):
        dist=a.distance(b)
        checks.append({'check':name,'measured_mm':round(dist,6),'target_mm':target,
                       'status':'PASS_NOMINAL' if dist>=target else 'REVIEW','method':'OCCT BRep minimum distance','note':note})
    chainstays=compound([v for k,v in members.items() if k.startswith('Chainstay')])
    seatstays=compound([v for k,v in members.items() if k.startswith('Seatstay')])
    gap('Rear tire to chainstays',tire_shapes['Rear_Wheel'],chainstays,6)
    gap('Rear tire to seatstays',tire_shapes['Rear_Wheel'],seatstays,6)
    gap('Rear tire to seat tube',tire_shapes['Rear_Wheel'],members['SeatTube'],6)
    gap('Front tire to down tube',tire_shapes['Front_Wheel'],members['DownTube'],6)
    gap('Front tire to fork',tire_shapes['Front_Wheel'],shapes['Front_Fork'],6)
    gap('Chainring envelope to chainstays',ring_shape,chainstays,3,'3 mm is an internal concept target, not supplied by brief.')
    gap('Chain strands to chainstays',shapes['Chain_Path'],chainstays,1,'Only two straight strands; links, slack and shifts not modeled.')
    # Solid swept crank-arm disks conservatively include every crank rotation.
    crank_sweep=compound([ring([0,sign*75,0],181.5,1,18) for sign in [-1,1]])
    gap('Full crank-arm sweep to frame',crank_sweep,shapes['Road_Frame'],3,'172.5 mm crank +9 mm arm radius; 18 mm-wide swept disk excludes spindle contacts.')
    # Tire steering samples are discrete. Pedals/toes and cable stops not represented.
    steering=[]
    for angle in range(-35,36,5):
        turned=tire_shapes['Front_Wheel'].rotate(tuple(crown),tuple(add(crown,u)),angle)
        steering.append({'steer_deg':angle,'gap_mm':round(turned.distance(shapes['Road_Frame']),6)})
    checks.append({'check':'Front tire steering samples to frame','measured_mm':min(v['gap_mm'] for v in steering),
                   'target_mm':6,'status':'PASS_SAMPLED' if min(v['gap_mm'] for v in steering)>=6 else 'REVIEW',
                   'method':'BRep distance at -35..+35 degrees, 5 degree increments','note':'Discrete samples do not prove continuous swept clearance.'})
    # Confirm exchange imports retain solids and volume rather than only a filename.
    roundtrip=[]
    for item in manifest:
        imported=cq.importers.importStep(str(ROOT/item['step_path'])).val()
        roundtrip.append({'name':item['name'],'valid':imported.isValid(),'solid_count':len(imported.Solids()),
                          'volume_relative_error':abs(imported.Volume()-item['volume_mm3'])/item['volume_mm3']})
    imported_assy=cq.importers.importStep(str(ROOT/'02_Assemblies/Bicycle_Main_Assembly.step')).val()
    result={'status':'NOMINAL CONCEPT GEOMETRY ONLY','checks':checks,'steering_samples':steering,
            'exported_components':manifest,'step_roundtrip':roundtrip,'assembly_roundtrip_valid':imported_assy.isValid(),
            'assembly_roundtrip_solids':len(imported_assy.Solids()),
            'unverified':['Native SolidWorks rebuild and mates','Continuous steering and drivetrain motion',
                'Actual supplier tires, rims, hubs, bearings, brakes, gears and pedals','Toe overlap and rider fit',
                'Welds, bent stays, tolerances and deformation','Static strength, fatigue, impact and applicable testing']}
    (ROOT/'04_Reference_Data/validation_results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'04_Reference_Data/clearance_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['check','measured_mm','target_mm','status','method','note']);w.writeheader();w.writerows(checks)
    assert all(i['valid'] for i in manifest), 'Invalid source shape'
    assert all(i['valid'] and i['volume_relative_error']<1e-6 for i in roundtrip), 'STEP round-trip failed'
    assert imported_assy.isValid(), 'Invalid assembly round-trip'
    print(json.dumps(checks,indent=2),flush=True)
    # CAD-derived rendering, not an AI image. VTK offscreen renderer uses tessellated model.
    import vtk
    renderer=vtk.vtkRenderer();renderer.SetBackground(0.95,0.96,0.97)
    for name,s,color in display:
        verts,faces=s.tessellate(1.0,0.15);points=vtk.vtkPoints();cells=vtk.vtkCellArray()
        for pt in verts:points.InsertNextPoint(*pt.toTuple())
        for tri in faces:
            cells.InsertNextCell(3)
            for index in tri:cells.InsertCellPoint(index)
        mesh=vtk.vtkPolyData();mesh.SetPoints(points);mesh.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(mesh);normals.ComputePointNormalsOn()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color);actor.GetProperty().SetSpecular(0.25);actor.GetProperty().SetSpecularPower(20)
        renderer.AddActor(actor)
    window=vtk.vtkRenderWindow();window.AddRenderer(renderer);window.SetSize(1600,1000);window.SetOffScreenRendering(1)
    cam=renderer.GetActiveCamera();cam.SetPosition(1800,-2600,1450);cam.SetFocalPoint(90,0,210);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();renderer.ResetCamera();cam.Zoom(1.18)
    window.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(ROOT/'03_Drawings/Bicycle_Concept_Preview.png'));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()
    print('CAD build, exchange round-trip, nominal checks and preview complete.',flush=True)

if __name__=='__main__':main()
