"""Single source of truth for concept geometry; millimetres and degrees."""
from pathlib import Path
import math, json, csv

ROOT = Path(__file__).resolve().parents[1]
def add(a,b): return [x+y for x,y in zip(a,b)]
def mul(a,k): return [x*k for x in a]
def main():
    # Advertised design inputs live here. Supporting stay/cockpit silhouettes are
    # explicit concept constants below and still require engineering on redesign.
    params={'wheelbase_mm':990,'head_angle_deg':73,'seat_angle_deg':73.5,'bb_drop_mm':70,
            'chainstay_mm':410,'wheel_od_mm':680,'tire_width_mm':25,'bead_seat_diameter_mm':622,
            'seat_tube_cc_mm':520,'head_tube_mm':140,'fork_offset_mm':45,'fork_axle_crown_mm':370,
            'lower_headset_stack_mm':12,'down_tube_junction_offset_mm':35,'front_hub_width_mm':100,
            'rear_hub_width_mm':130,'bb_shell_width_mm':68,'bb_shell_od_mm':40,'bb_shell_id_mm':34,
            'crank_length_mm':172.5,'chainring_radius_mm':105,'chainring_y_mm':-45,
            'chainring_thickness_mm':4,'rear_sprocket_radius_mm':35,'rear_sprocket_y_mm':-45,
            'illustrative_chainring_teeth':50,'illustrative_sprocket_teeth':17,'steering_check_deg':35,
            'target_min_tire_clearance_mm':6}
    assert 0 < params['head_angle_deg'] < 90 and 0 < params['seat_angle_deg'] < 90
    assert params['chainstay_mm'] > params['bb_drop_mm'] >= 0
    assert params['fork_axle_crown_mm'] > abs(params['fork_offset_mm'])
    assert params['wheel_od_mm'] > params['bead_seat_diameter_mm'] > 0
    assert 0 < params['tire_width_mm'] < params['wheel_od_mm']/2
    assert 0 < params['bb_shell_id_mm'] < params['bb_shell_od_mm']
    assert params['bb_shell_width_mm'] > 16
    assert params['front_hub_width_mm'] > 26 and params['rear_hub_width_mm'] > 0
    assert params['chainring_radius_mm'] > 20 and params['rear_sprocket_radius_mm'] > 20
    assert params['chainring_thickness_mm'] > 0 and params['crank_length_mm'] > 0
    assert params['steering_check_deg'] >= 0
    assert 0 <= params['down_tube_junction_offset_mm'] <= params['head_tube_mm']
    ha, sa = map(math.radians, [params['head_angle_deg'],params['seat_angle_deg']])
    u=[-math.cos(ha),0,math.sin(ha)]
    n=[math.sin(ha),0,math.cos(ha)]
    rear=[-math.sqrt(params['chainstay_mm']**2-params['bb_drop_mm']**2),0,params['bb_drop_mm']]
    front=add(rear,[params['wheelbase_mm'],0,0])
    crown=add(add(front,mul(u,math.sqrt(params['fork_axle_crown_mm']**2-params['fork_offset_mm']**2))),mul(n,-params['fork_offset_mm']))
    hlo=add(crown,mul(u,params['lower_headset_stack_mm'])); hhi=add(hlo,mul(u,params['head_tube_mm']))
    seat=[-params['seat_tube_cc_mm']*math.cos(sa),0,params['seat_tube_cc_mm']*math.sin(sa)]
    pts={'BB':[0,0,0], 'RearAxle':rear, 'FrontAxle':front,
         'ForkCrown':crown,'HeadLower':hlo,'HeadUpper':hhi,
         'SeatTop':seat,'DownTubeHead':add(hlo,mul(u,params['down_tube_junction_offset_mm']))}
    for side, sign in [('L',1),('R',-1)]:
        pts.update({f'ChainStart{side}':[0,sign*(params['bb_shell_width_mm']/2-8),0],
                    f'ChainKnee1{side}':[-110,sign*30,34],
                    f'ChainKnee2{side}':[-180,sign*40,50],
                    f'RearDropout{side}':add(rear,[0,sign*params['rear_hub_width_mm']/2,0]),
                    f'SeatStayStart{side}':add(seat,[0,sign*12,0]),
                    f'ForkShoulder{side}':add(crown,[0,sign*(params['front_hub_width_mm']/2-13),0]),
                    f'FrontDropout{side}':add(front,[0,sign*params['front_hub_width_mm']/2,0])})
    members=[{'name':'SeatTube','start':'BB','end':'SeatTop','od_mm':28.6,'wall_mm':1.0},
             {'name':'TopTube','start':'SeatTop','end':'HeadUpper','od_mm':28.6,'wall_mm':0.9},
             {'name':'DownTube','start':'BB','end':'DownTubeHead','od_mm':35.0,'wall_mm':1.1},
             {'name':'HeadTube','start':'HeadLower','end':'HeadUpper','od_mm':38.0,'wall_mm':2.0}]
    for side in ['L','R']:
        for k,(a,b) in enumerate([(f'ChainStart{side}',f'ChainKnee1{side}'),(f'ChainKnee1{side}',f'ChainKnee2{side}'),(f'ChainKnee2{side}',f'RearDropout{side}')],1):
            members.append({'name':f'Chainstay{side}{k}','start':a,'end':b,'od_mm':18,'wall_mm':1})
        members.append({'name':f'Seatstay{side}','start':f'SeatStayStart{side}','end':f'RearDropout{side}','od_mm':14,'wall_mm':0.9})
    d={'revision':'A','date':'2026-11-07','units':'mm','coordinate_system':'X forward; Y left; Z up; origin bottom bracket',
       'status':'CONCEPT ONLY - NOT FOR MANUFACTURE','pipeline':'Welded round-tube steel concept; grade and joint design unselected',
       'parameters':params,
       'derived':{'reach_mm':hhi[0],'stack_mm':hhi[2],
                  'effective_top_tube_mm':hhi[0]+hhi[2]/math.tan(sa),
                  'trail_mm':(params['wheel_od_mm']/2*math.cos(ha)-params['fork_offset_mm'])/math.sin(ha),
                  'bb_ground_height_mm':params['wheel_od_mm']/2-params['bb_drop_mm']},
       'steering_axis':u,'points':pts,'frame_members':members,
       'assumptions':['Medium-size layout; rider fit not evaluated.',
          '680 mm OD x 25 mm width is a design envelope, not a verified supplier tire.',
          '100/130 mm hub spacing and rim-brake layout are project assumptions, not a purchased-system specification.',
          'Tube sections are nominal modelling values, not strength-qualified dimensions.',
          'Stay bends, dropout detail, bearing seats, brake mounts, welds and threads require detailed engineering.',
          'Supplier components are simplified reference geometry; no supplier CAD imported.']}
    out=ROOT/'04_Reference_Data'
    (out/'design_parameters.json').write_text(json.dumps(d,indent=2)+'\n')
    with (out/'reference_points.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['point','x_mm','y_mm','z_mm']); w.writerows([k,*[round(v,6) for v in p]] for k,p in pts.items())
    with (out/'tube_schedule.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['member','start_point','end_point','OD_mm','wall_mm','centerline_length_mm','note'])
        for m in members: w.writerow([m['name'],m['start'],m['end'],m['od_mm'],m['wall_mm'],round(math.dist(pts[m['start']],pts[m['end']]),3),'Reference length before coping; not a cut length'])
    print(json.dumps(d['derived'],indent=2))
if __name__=='__main__': main()
