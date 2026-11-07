"""Regenerate the concept drawing set from the project's shared geometry data."""
from pathlib import Path
import csv, json, math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '04_Reference_Data'
OUT = ROOT / '03_Drawings' / 'Road_Bicycle_Design_Project.pdf'
D = json.loads((DATA / 'design_parameters.json').read_text(encoding='utf-8-sig'))
P, Q, DER = D['points'], D['parameters'], D['derived']
VALIDATION = {}
vp = DATA / 'validation_results.json'
if vp.exists():
    VALIDATION = json.loads(vp.read_text(encoding='utf-8-sig'))
CHECKS = {v['check']: v for v in VALIDATION.get('checks', [])}
def result_mm(name, fallback):
    return CHECKS.get(name, {}).get('measured_mm', fallback)
HAS_EXACT = bool(CHECKS)
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
W,H = 1190.551,841.89
INK, MUTED = HexColor('#132D42'), HexColor('#596F7B')
BLUE, CYAN = HexColor('#075B86'), HexColor('#3C9CAD')
ORANGE, PAPER, LINE = HexColor('#CC693B'), HexColor('#F7F6F0'), HexColor('#CCD6D7')
PALE, DARK = HexColor('#EAF0F1'), HexColor('#102D3F')
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Road Bicycle Design Project | Concept Engineering Package | Revision A')
c.setAuthor('Bicycle Design Project')
c.setSubject('Dimensioned concept drawings, design assumptions and verification status')

def text(x,y,s,size=10,font='Arial',color=INK,align='left'):
    c.setFont(font,size); c.setFillColor(color)
    if align == 'right': c.drawRightString(x,y,str(s))
    elif align == 'center': c.drawCentredString(x,y,str(s))
    else: c.drawString(x,y,str(s))

def para(x,y,s,width,size=10,leading=None,color=INK,bold=False):
    st=ParagraphStyle('p',fontName='Arial-Bold' if bold else 'Arial',fontSize=size,
                      leading=leading or size*1.42,textColor=color,alignment=TA_LEFT)
    ob=Paragraph(s,st); aw,ah=ob.wrap(width,1000); ob.drawOn(c,x,y-ah); return ah

def line(a,b,color=LINE,width=1,dash=None):
    c.setStrokeColor(color); c.setLineWidth(width); c.setDash(dash or [])
    c.line(a[0],a[1],b[0],b[1]); c.setDash([])

def rect(x,y,w,h,fill=PALE,stroke=None,r=0):
    c.setFillColor(fill); c.setStrokeColor(stroke or fill)
    if r: c.roundRect(x,y,w,h,r,fill=1,stroke=bool(stroke))
    else: c.rect(x,y,w,h,fill=1,stroke=bool(stroke))

def circle(x,y,r,fill=None,stroke=INK,width=1):
    c.setLineWidth(width); c.setStrokeColor(stroke); c.setFillColor(fill or white)
    c.circle(x,y,r,fill=fill is not None,stroke=1)

def poly(points,color=BLUE,width=1,closed=False,fill=None):
    path=c.beginPath();path.moveTo(*points[0])
    for p in points[1:]:path.lineTo(*p)
    if closed:path.close()
    c.setStrokeColor(color);c.setLineWidth(width)
    if fill:c.setFillColor(fill)
    c.drawPath(path,stroke=1,fill=fill is not None)

def label(x,y,s,size=10,color=INK):
    tw=pdfmetrics.stringWidth(s,'Arial',size)
    rect(x-tw/2-4,y-3,tw+8,size+6,PAPER)
    text(x,y,s,size,color=color,align='center')

def arrow(pt,direction,size=5,color=MUTED):
    ux,uy=direction; norm=math.hypot(ux,uy);ux/=norm;uy/=norm
    a=(pt[0]+size*ux+size*.35*uy,pt[1]+size*uy-size*.35*ux)
    b=(pt[0]+size*ux-size*.35*uy,pt[1]+size*uy+size*.35*ux)
    poly([pt,a,b],color,.7,True,color)

def dim(a,b,offset,s,label_shift=0,color=MUTED):
    dx,dy=b[0]-a[0],b[1]-a[1];n=math.hypot(dx,dy);ux,uy=dx/n,dy/n;nx,ny=-uy,ux
    aa=(a[0]+nx*offset,a[1]+ny*offset);bb=(b[0]+nx*offset,b[1]+ny*offset)
    line(a,(aa[0]+nx*4,aa[1]+ny*4),color,.55);line(b,(bb[0]+nx*4,bb[1]+ny*4),color,.55)
    line(aa,bb,color,.65);arrow(aa,(ux,uy),color=color);arrow(bb,(-ux,-uy),color=color)
    mid=((aa[0]+bb[0])/2+nx*label_shift,(aa[1]+bb[1])/2+ny*label_shift)
    angle=math.degrees(math.atan2(dy,dx));
    if angle>90 or angle< -90:angle+=180
    c.saveState();c.translate(*mid);c.rotate(angle);label(0,3,s,9.5,color);c.restoreState()

def hdim(a,b,y,s):
    line(a,(a[0],y-4),MUTED,.55);line(b,(b[0],y-4),MUTED,.55)
    line((a[0],y),(b[0],y),MUTED,.7);arrow((a[0],y),(1,0));arrow((b[0],y),(-1,0));label((a[0]+b[0])/2,y+5,s)

def vdim(a,b,x,s):
    line(a,(x+4,a[1]),MUTED,.55);line(b,(x+4,b[1]),MUTED,.55)
    line((x,a[1]),(x,b[1]),MUTED,.7);arrow((x,a[1]),(0,1));arrow((x,b[1]),(0,-1))
    c.saveState();c.translate(x+5,(a[1]+b[1])/2);c.rotate(90);label(0,0,s,9);c.restoreState()

def leader(point,elbow,end,s,size=9,color=MUTED):
    line(point,elbow,color,.7);line(elbow,end,color,.7);circle(*point,1.5,color,color,.5)
    left=end[0]<elbow[0]
    text(end[0]-4 if left else end[0]+4,end[1]-3,s,size,color=color,align='right' if left else 'left')

def header(num,title,subtitle):
    rect(0,0,W,H,PAPER);text(42,H-34,'BICYCLE / DESIGN ENGINEERING',9,'Arial-Bold',BLUE)
    text(W-42,H-34,'REV A  /  07 NOV 2026',9,color=MUTED,align='right')
    text(42,H-77,title,27,'Arial-Bold');text(43,H-99,subtitle,10,color=MUTED)
    line((42,H-115),(W-42,H-115),LINE,.8)

def footer(num):
    line((42,56),(W-42,56),LINE,.8)
    text(42,37,'CONCEPT ONLY - NOT FOR MANUFACTURE',9,'Arial-Bold',ORANGE)
    text(W/2,37,'Views not to scale | All dimensions mm | Nominal geometry | A3 landscape',8,color=MUTED,align='center')
    text(W-42,37,f'BDP-A-{num:02d}  /  {num:02d} of 06',8.5,color=MUTED,align='right');c.showPage()

def kicker(x,y,s):text(x,y,s,9,'Arial-Bold',BLUE)

def table(x,top,width,headers,rows,colfractions,rowh=23,fs=9):
    widths=[width*f for f in colfractions];rect(x,top-29,width,29,DARK)
    xx=x
    for h,ww in zip(headers,widths):text(xx+9,top-19,h,fs,'Arial-Bold',white);xx+=ww
    y=top-29
    for i,row in enumerate(rows):
        rect(x,y-rowh,width,rowh,white if i%2==0 else PALE)
        xx=x
        for cell,ww in zip(row,widths):text(xx+9,y-rowh/2-3,str(cell),fs);xx+=ww
        y-=rowh
    return y

def project(p,ox=410,oy=391,s=.36):
    x,y,z=p;return (ox+s*(.95*x-.62*y),oy+s*(z+.24*x+.29*y))

def projected_bike():
    proj=project
    # Pale floor and two thin projected wheels.
    for axle in [P['RearAxle'],P['FrontAxle']]:
        for rad,col,lw in [(340,INK,8),(327,PAPER,3),(311,MUTED,2)]:
            pts=[proj((axle[0]+rad*math.cos(t),0,axle[2]+rad*math.sin(t))) for t in [i*2*math.pi/150 for i in range(151)]]
            poly(pts,col,lw)
        for i in range(18):
            a=i*2*math.pi/18;line(proj(axle),proj((axle[0]+309*math.cos(a),0,axle[2]+309*math.sin(a))),LINE,.6)
        circle(*proj(axle),4,INK,INK)
    for m in D['frame_members']:
        line(proj(P[m['start']]),proj(P[m['end']]),BLUE,max(3,m['od_mm']*.47))
        line(proj(P[m['start']]),proj(P[m['end']]),CYAN,max(1,m['od_mm']*.13))
    for side in ['L','R']:
        line(proj(P['ForkCrown']),proj(P['ForkShoulder'+side]),BLUE,9)
        line(proj(P['ForkShoulder'+side]),proj(P['FrontDropout'+side]),BLUE,10)
    # Schematic reference components.
    st=P['SeatTop'];seatpost=(st[0]-42,0,st[2]+142)
    line(proj(st),proj(seatpost),MUTED,8)
    line(proj((seatpost[0]-70,0,seatpost[2]+5)),proj((seatpost[0]+92,0,seatpost[2]+5)),INK,14)
    hu=P['HeadUpper'];stem=(hu[0]+90,0,hu[2]+76)
    line(proj(hu),proj((hu[0]-14,0,hu[2]+48)),MUTED,9)
    line(proj((hu[0]-14,0,hu[2]+48)),proj(stem),MUTED,9)
    bars=[(stem[0],-190,stem[2]),(stem[0]+85,-190,stem[2]-8),(stem[0]+110,-190,stem[2]-90),(stem[0]+60,-190,stem[2]-126)]
    poly([proj(p) for p in bars],INK,7)
    poly([proj((p[0],-p[1],p[2])) for p in bars],INK,7)
    line(proj((stem[0],-190,stem[2])),proj((stem[0],190,stem[2])),INK,7)
    for rad in [105,86]:
        poly([proj((rad*math.cos(i*2*math.pi/80),-45,rad*math.sin(i*2*math.pi/80))) for i in range(81)],MUTED,2)
    for sign in [-1,1]:
        endpoint=(sign*110,-58,sign*-133)
        line(proj((0,-58,0)),proj(endpoint),INK,6)
        line(proj((endpoint[0]-25,-58,endpoint[2])),proj((endpoint[0]+25,-100,endpoint[2])),INK,7)

# 01 / Overview
header(1,'Road bicycle concept','A coherent 700c layout, transparent assumptions and a reproducible CAD handoff.')
rect(42,189,780,514,HexColor('#EDF1EF'),r=8)
projected_bike()
text(62,211,'SCHEMATIC AXONOMETRIC VIEW',9,'Arial-Bold',BLUE)
text(62,196,'Vector projection from the master coordinates; reference components are illustrative.',8,color=MUTED)
x=850
kicker(x,690,'DESIGN ENVELOPE')
for yy,val,cap in [(644,'990 mm','Wheelbase'),(566,'73.0° / 73.5°','Head / seat tube angle'),(488,'410 mm','Chainstay, axle to BB'),(410,'70 mm','Bottom bracket drop')]:
    text(x,yy,val,26,'Arial-Bold',BLUE);text(x,yy-21,cap,11,color=MUTED)
line((x,366),(W-42,366),LINE)
para(x,346,'Medium-size welded round-tube steel concept. Tube grade, detailed joints and rider fit remain unselected.',286,11)
para(x,267,'Rim-brake layout and 100 / 130 mm hub spacing are assumed. No supplier CAD has been imported.',286,10,color=MUTED)
for xx,title,body in [(42,'01  Geometry','Shared coordinates drive the frame layout, nominal tubes and component envelopes.'),(414,'02  Exchange model','STEP geometry supports review and import into a mechanical CAD environment.'),(786,'03  Native handoff','SolidWorks creation is scripted but unexecuted. Native features and mates require local verification.')]:
    kicker(xx,154,title);para(xx,138,body,330,10)
footer(1)

# 02 / Dimensioned side elevation
header(2,'Master geometry / side elevation','Right-side schematic elevation | Dimensions define the master skeleton, not tube cut lengths.')
s=.56;ox=465;oy=382
S=lambda p:(ox+s*p[0],oy+s*p[2])
for ax in ['RearAxle','FrontAxle']:
    a=S(P[ax]);circle(*a,340*s,stroke=HexColor('#82959A'),width=1.4);circle(*a,311*s,stroke=LINE,width=.7)
    line((a[0]-9,a[1]),(a[0]+9,a[1]),MUTED,.7);line((a[0],a[1]-9),(a[0],a[1]+9),MUTED,.7)
line((70,oy+70*s),(W-70,oy+70*s),LINE,.7,[5,4]);text(73,oy+70*s+7,'AXLE DATUM',8,color=MUTED)
line((70,oy-270*s),(W-70,oy-270*s),LINE,.8);text(73,oy-270*s+7,'NOMINAL GROUND',8,color=MUTED)
for m in D['frame_members']:
    if 'R' not in m['name']:line(S(P[m['start']]),S(P[m['end']]),BLUE,2.2)
line(S(P['HeadLower']),S(P['FrontAxle']),BLUE,2.2)
line(S(P['HeadUpper']),S([P['FrontAxle'][0]-45/ math.cos(math.radians(17)),0,70]),CYAN,.8,[4,3])
for name in ['BB','SeatTop','HeadLower','HeadUpper','RearAxle','FrontAxle']:
    circle(*S(P[name]),2.4,PAPER,BLUE,.9)
hdim(S(P['RearAxle']),S(P['FrontAxle']),189,'990 WHEELBASE')
dim(S(P['RearAxle']),S(P['BB']),-47,'410 CHAINSTAY')
dim(S(P['BB']),S(P['SeatTop']),34,'520 C-C')
dim(S(P['SeatTop']),S(P['HeadUpper']),27,'541.6 TOP TUBE C-C')
dim(S(P['BB']),S(P['DownTubeHead']),-27,'619.0 DOWN TUBE C-C')
dim(S(P['HeadLower']),S(P['HeadUpper']),-37,'140 HEAD TUBE')
vdim(S(P['BB']),S([0,0,70]),1078,'70 BB DROP')
leader(S(P['RearAxle']), (170,493),(118,493),'REAR AXLE',8)
leader(S(P['BB']), (501,345),(535,345),'BB (0, 0, 0)',8)
leader(S([P['FrontAxle'][0]+300,0,230]),(1052,572),(1073,572),'Ø680',10)
# Correct angle arcs: acute angles from rearward horizontal to the tube axes.
bx,by=S(P['BB']);r=68;c.setStrokeColor(ORANGE);c.setLineWidth(1);c.arc(bx-r,by-r,bx+r,by+r,106.5,73.5)
line((bx-84,by),(bx-21,by),ORANGE,.6);label(bx-77,by+51,'73.5°',10,ORANGE)
hx,hy=S(P['HeadLower']);r=50
c.setStrokeColor(ORANGE);c.arc(hx-r,hy-r,hx+r,hy+r,107,73)
line((hx-67,hy),(hx,hy),ORANGE,.6);label(hx-51,hy+38,'73.0°',10,ORANGE)
rect(42,76,W-84,80,PALE,r=4)
vals=[('REACH',f"{DER['reach_mm']:.1f}"),('STACK',f"{DER['stack_mm']:.1f}"),('EFFECTIVE TOP TUBE',f"{DER['effective_top_tube_mm']:.1f}"),('FORK OFFSET',f"{Q['fork_offset_mm']:.0f}"),('GEOMETRIC TRAIL',f"{DER['trail_mm']:.1f}"),('BB GROUND HEIGHT',f"{DER['bb_ground_height_mm']:.0f}")]
for i,(lab,val) in enumerate(vals):
    xx=59+i*181;text(xx,131,lab,7.5,'Arial-Bold',MUTED);text(xx,104,val+' mm',18,'Arial-Bold',BLUE)
footer(2)

# 03 / Clearance and rear triangle
header(3,'Rear triangle / clearance intent','Orthographic projections establish the nominal path. Three-dimensional clearance results are reported separately.')
rect(42,366,710,340,white,r=5);kicker(62,682,'TOP PROJECTION / X-Y')
tx,ty,ts=637,539,.75
T=lambda p:(tx+ts*p[0],ty+ts*p[1])
# Tire silhouette in plan: circular-envelope projection, not a section.
rx=T(P['RearAxle'])[0];rect(rx-340*ts,ty-12.5*ts,680*ts,25*ts,HexColor('#DDE3E1'),r=9)
line((76,ty),(725,ty),MUTED,.6,[4,3])
for side in ['L','R']:
    poly([T(P[n+side]) for n in ['ChainStart','ChainKnee1','ChainKnee2','RearDropout']],BLUE,18*ts)
    poly([T(P[n+side]) for n in ['ChainStart','ChainKnee1','ChainKnee2','RearDropout']],CYAN,1)
    line(T(P['SeatStayStart'+side]),T(P['RearDropout'+side]),ORANGE,2)
    for n in ['ChainStart','ChainKnee1','ChainKnee2','RearDropout']:circle(*T(P[n+side]),2,PAPER,BLUE,.7)
line(T(P['RearDropoutL']),T(P['RearDropoutR']),MUTED,1)
vdim(T(P['RearDropoutR']),T(P['RearDropoutL']),rx-33,'130 HUB WIDTH')
vdim(T((0,-26,0)),T((0,26,0)),686,'52 STAY START C-C')
leader(T(P['ChainKnee2L']),(490,623),(555,623),'KNEE 2  (-180, ±40, 50)',8.5)
leader(T(P['ChainKnee1R']),(560,441),(590,441),'KNEE 1',8.5)
leader((rx+143,ty+9),(456,479),(472,479),'25 WIDE TIRE ENVELOPE',8.5)
text(62,397,'Blue: Ø18 chainstay path   Orange: seatstay projection',9,color=MUTED)
text(62,381,'Plan-view overlap does not indicate collision; Z must be included in the check.',8.5,color=MUTED)
rect(778,161,370,545,white,r=5);kicker(798,682,'REAR PROJECTION / Y-Z')
ry,rz,rs=961,348,.58
R=lambda p:(ry+rs*p[1],rz+rs*p[2])
rect(ry-12.5*rs,rz-270*rs,25*rs,680*rs,HexColor('#DDE3E1'),r=6)
line((ry,178),(ry,652),LINE,.7,[4,3])
for side in ['L','R']:
    line(R(P['SeatStayStart'+side]),R(P['RearDropout'+side]),ORANGE,14*rs)
    poly([R(P[n+side]) for n in ['ChainStart','ChainKnee1','ChainKnee2','RearDropout']],BLUE,18*rs)
line(R(P['RearDropoutL']),R(P['RearDropoutR']),MUTED,2)
hdim(R(P['RearDropoutR']),R(P['RearDropoutL']),316,'130')
hdim((ry-12.5*rs,rz-270*rs),(ry+12.5*rs,rz-270*rs),174,'25')
leader(R(P['SeatStayStartL']),(1010,642),(1040,642),'Ø14',9)
para(798,236,'Nominal tire silhouette.<br/>Rear projection does not show local three-dimensional gaps.',135,8.5,color=MUTED)
kicker(42,337,'DESIGN TARGET: AT LEAST 6 mm TIRE-TO-FRAME GAP')
analytical=[(f"{result_mm('Rear tire to chainstays',7.378):.3f}",'REAR TIRE / CHAINSTAY'),(f"{result_mm('Rear tire to seat tube',13.163):.3f}",'REAR TIRE / SEAT TUBE'),(f"{result_mm('Front tire to down tube',23.644):.3f}",'FRONT TIRE / DOWN TUBE')]
for i,(val,lab) in enumerate(analytical):
    xx=42+i*239;rect(xx,217,224,98,PALE,r=4);text(xx+15,282,val+' mm',24,'Arial-Bold',BLUE);text(xx+15,260,lab,7.5,'Arial-Bold',MUTED);text(xx+15,237,'OCCT nominal BRep distance' if HAS_EXACT else 'Analytical nominal-envelope result',8,color=MUTED)
gap_method='OCCT boundary-representation minimum distances' if HAS_EXACT else 'Analytical distances'
para(42,194,f'{gap_method} use nominal tubes and the specified 680 × 25 mm tire envelope. They exclude manufacturing tolerances, wheel flex, inflation growth, debris and supplier-specific tire shape. The plan projections are not clearance sections.',710,10)
para(42,111,'The brief describes ~680 mm as a true 700x25c envelope. Here it is a project assumption: 25-622 identifies nominal tire width and bead-seat diameter; actual mounted dimensions depend on the tire/rim combination.',1100,9,color=MUTED)
footer(3)

# 04 / Definition and schedules
header(4,'Coordinate definition / member schedule','Single source of truth: design_parameters.json, reference_points.csv and tube_schedule.csv.')
kicker(42,697,'MASTER POINTS / MM')
rows=[]
for name,p in P.items():rows.append([name]+[f'{n:.2f}' for n in p])
table(42,680,544,['POINT','X','Y','Z'],rows,[.46,.18,.18,.18],rowh=20,fs=8.7)
kicker(616,697,'TUBE SCHEDULE / NOMINAL SECTION')
with (DATA/'tube_schedule.csv').open(encoding='utf-8-sig',newline='') as f: tube=list(csv.DictReader(f))
rows=[[r['member'],r['OD_mm'],r['wall_mm'],f"{float(r['centerline_length_mm']):.1f}"] for r in tube]
bottom=table(616,680,532,['MEMBER','OD','WALL','C-LENGTH'],rows,[.46,.16,.16,.22],rowh=23,fs=9)
para(616,bottom-18,'All lengths are centerline references before coping. They are not fabrication cut lengths. Nominal walls are modelling inputs and have not been strength-qualified.',532,10,color=MUTED)
kicker(616,282,'CONCEPT DATUM STRATEGY')
para(616,265,'Origin: bottom bracket center. X points forward, Y to the rider\'s left and Z upward. The frame center plane is Y = 0. Axles are parallel to Y; both nominal axle centers lie at Z = 70.',532,10)
para(616,193,'Proposed inspection references: BB axis, frame median plane, rear axle axis. Detailed datum features, fit tolerances, dropout parallelism and weld-distortion allowances require a manufacturing design.',532,10)
rect(42,89,544,87,PALE,r=4)
text(58,151,'PROVENANCE',9,'Arial-Bold',BLUE)
para(58,137,'The brief controls wheelbase range, tube angles, BB drop and chainstay range. All other values are explicit design assumptions. Left / right stay paths are mirrored about Y = 0.',512,9.5)
footer(4)

# 05 / Assembly and purchased components
header(5,'Assembly plan / component interfaces','SolidWorks implementation intent. Mates below are specified for the native handoff and have not been executed or validated.')
kicker(42,697,'ASSEMBLY CONSTRAINT PLAN')
mate_rows=[
['Frame','Fix origin / orientation','0','Use the skeleton as the grounded reference'],
['Fork + steering','Concentric + axial position','1 rotation','Do not lock the steering concentric mate'],
['Front wheel','Concentric + width/center','1 rotation','Center in nominal 100 mm front dropout gap'],
['Rear wheel','Concentric + width/center','1 rotation','Center in nominal 130 mm rear dropout gap'],
['Crank axle','Concentric + axial position','1 rotation','Use BB shell axis, nominal 68 mm width'],
['Crank / rear drive','Illustrative gear relation','Coupled','50:17 example; verify direction and ratio'],
['Cockpit / saddle','Placement / rigid group','0 intended','Reference geometry only; final interfaces TBD']]
table(42,680,1106,['COMPONENT','MATE INTENT','REMAINING DOF','IMPLEMENTATION NOTE'],mate_rows,[.17,.27,.13,.43],rowh=31,fs=9.3)
para(42,414,'A gear mate is a simplified kinematic relation. It does not reproduce chain contact, derailleur shifting, backlash or freehub coasting. Wheel rotation, steering and drivetrain motion must be exercised in SolidWorks after native mate creation.',1106,10,color=MUTED)
kicker(42,355,'PURCHASED-COMPONENT REGISTER / UNSELECTED')
comp=[['Tire + rim','25-622 class; 680 × 25 envelope','Verify mounted width/OD and rim compatibility'],['Front / rear hubs','100 / 130 mm nominal spacing','Select axle format, dropouts and hub CAD'],['Headset + fork','45 offset; 370 axle-to-crown','Confirm steerer, bearing seats and headset stack'],['Bottom bracket + crank','68 shell; 172.5 crank; 50T example','Select shell standard, chainline and pedal clearance'],['Brake / drivetrain / cockpit','Rim-brake concept; 17T rear example','Add mounts, cable routes and supplier interfaces']]
table(42,338,1106,['SYSTEM','CURRENT ASSUMPTION','REQUIRED BEFORE DETAIL DESIGN'],comp,[.24,.31,.45],rowh=33,fs=9.5)
rect(42,86,1106,54,PALE,r=4)
para(58,124,'No commercial parts are claimed to be sourced, licensed, purchase-ready or supplier-approved. Supplier models must be checked for revision, units, origin, envelope accuracy and permitted use before integration.',1075,10)
footer(5)

# 06 / Validation and handoff
header(6,'Validation record / release boundary','Nominal model verification and exchange-file evidence. Native CAD completion and manufacturing release remain open.')
kicker(42,697,'EVIDENCE AND STATUS')
vrows=[
['Geometry targets','Defined','990 WB; 73° HA; 73.5° STA; 70 drop; 410 CS'],
['Tube coordinates / sections','Defined','Parametric point data and nominal tube schedule'],
['Rear tire / chainstay gap','Analytical','7.378 mm nominal-envelope result; target >= 6 mm'],
['Chainring / chainstay gap','Analytical','4.344 mm envelope result; no design criterion assigned'],
['STEP geometry checks','See validation file','Exact checks recorded in validation_results.json when generated'],
['SolidWorks part / assembly','Not executed','Native feature tree, constraints and rebuild require SolidWorks'],
['Dynamic interference','Not completed','Full pedal, steering, chain and wheel motion sweep required'],
['Fit / structure / durability','Not evaluated','Rider fitting, loads, material, joints and physical tests required'],
['Manufacturing GD&T','Not released','Datums, tolerances, welds, bends and inspection plan pending']]
if HAS_EXACT:
    vrows=[]
    for ck in VALIDATION['checks']:
        status={'PASS_NOMINAL':'Pass at nominal geometry','PASS_SAMPLED':'Pass at discrete steering samples','REVIEW':'Review required'}.get(ck['status'],ck['status'])
        if 'Chainring' in ck['check']: status+='; internal 3 mm target'
        elif 'Chain strands' in ck['check']: status+='; two straight strands only'
        elif 'crank' in ck['check'].lower(): status+='; conservative crank-arm disks'
        vrows.append([ck['check'],f"{ck['measured_mm']:.3f} mm",f">= {ck['target_mm']} mm",status])
    rt=VALIDATION.get('step_roundtrip',[])
    good=all(v.get('valid',False) and v.get('volume_relative_error',1)<1e-6 for v in rt)
    ast=VALIDATION.get('assembly_roundtrip_valid',False)
    vrows += [
        ['STEP export / reimport',f'{len(rt)} components','Valid BReps','Passed; assembly valid' if good and ast else 'See validation_results.json'],
        ['SolidWorks rebuild / mates','Not executed','Native review','No native feature or mate validation available'],
        ['Fit / structural performance','Not evaluated','Engineering','Rider fit, material, joints, loads and physical tests required'],
        ['Manufacturing drawing release','Not released','Detail design','Tolerances, welds, interfaces and inspection plan pending']]
    table(42,680,1106,['CHECK','RESULT','TARGET','STATUS / LIMITATION'],vrows,[.30,.13,.12,.45],rowh=22,fs=8.9)
else:
    table(42,680,1106,['CHECK','STATUS','EVIDENCE / LIMITATION'],vrows,[.26,.18,.56],rowh=29,fs=9.3)
if HAS_EXACT:
    para(42,349,'Distances are OCCT BRep minimum distances. Steering uses -35° to +35° at 5° increments; no continuous sweep is proven. Chainring / crank / chain-strand targets of 3 / 3 / 1 mm are internal concept criteria.',1106,8.8,color=MUTED)
kicker(42,310,'CAD COMPLETION SEQUENCE')
steps=[('1','Import and rebuild','Open the STEP model or execute the supplied native-creation automation. Confirm mm units, origins, orientation and reference planes.'),('2','Resolve interfaces','Select actual tires, hubs, drivetrain, headset and brakes. Replace reference envelopes and complete joints, bends, dropouts and bearing details.'),('3','Validate and release','Resolve intentional overlaps, run static and dynamic interference, establish tolerance budgets and structural tests, then create controlled manufacturing drawings.')]
for i,(n,head,body) in enumerate(steps):
    xx=42+i*375;circle(xx+14,278,13,BLUE,BLUE);text(xx+14,274,n,11,'Arial-Bold',white,'center');text(xx+36,274,head,12,'Arial-Bold')
    para(xx,250,body,340,10)
line((42,190),(W-42,190),LINE)
kicker(42,170,'REFERENCES / DESIGN INTERPRETATION')
para(42,153,'Project brief: original_brief.md (provided by the user). Geometry and modelling assumptions: design_parameters.json. Nominal tire sizing guidance: Schwalbe Technology FAQ and Tire Sizes Overview. CAD exchange workflow: CadQuery import/export documentation.',1106,9,color=MUTED)
urls=[('Schwalbe sizing FAQ','https://www.schwalbetires.com/technology-faq/'),('Schwalbe tire-size overview','https://www.schwalbe.com/media/97/93/b4/1700219698/Reifengroessen-uebersicht_EN.pdf'),('CadQuery import/export','https://github.com/CadQuery/cadquery/blob/master/doc/importexport.rst')]
xx=42
for name,url in urls:
    text(xx,91,name,9,color=BLUE);ww=pdfmetrics.stringWidth(name,'Arial',9);c.linkURL(url,(xx,88,xx+ww,103),relative=0);xx+=350
footer(6)
c.save()
print(OUT)
