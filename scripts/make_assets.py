"""Render original NexRoute brand and relationship-diagram images."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets'
A.mkdir(exist_ok=True)
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 108" role="img" aria-label="NexRoute Logistics Intelligence logo">
<rect width="420" height="108" fill="#0B1420"/>
<g transform="translate(14,18)" fill="none" stroke-linejoin="round" stroke-linecap="round">
<path d="M10 57 L35 32 L61 49 L83 13" stroke="#2DD4BF" stroke-width="9"/>
<path d="M67 13 H83 V29" stroke="#4C9AFF" stroke-width="9"/>
<circle cx="10" cy="57" r="7" fill="#4C9AFF" stroke="#0B1420" stroke-width="3"/>
<circle cx="35" cy="32" r="7" fill="#2DD4BF" stroke="#0B1420" stroke-width="3"/>
</g><text x="115" y="57" font-family="Arial,sans-serif" font-size="36" font-weight="700" fill="#E8EEF5">NEX<tspan fill="#2DD4BF">ROUTE</tspan></text>
<text x="116" y="79" font-family="Arial,sans-serif" font-size="13" letter-spacing="2.6" fill="#95A7B8">LOGISTICS INTELLIGENCE</text></svg>'''
(A/'nexroute_logo.svg').write_text(svg,encoding='utf-8')
img=Image.new('RGB',(840,216),'#0B1420')
d=ImageDraw.Draw(img)
d.line([(45,151),(83,92),(137,121),(180,42)],fill='#2DD4BF',width=15,joint='curve')
d.line([(150,42),(180,42),(180,73)],fill='#4C9AFF',width=13,joint='curve')
for x,y,c in [(45,151,'#4C9AFF'),(83,92,'#2DD4BF')]:d.ellipse((x-11,y-11,x+11,y+11),fill=c)
try:
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',66)
 small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
except OSError:font=ImageFont.load_default();small=font
d.text((238,69),'NEXROUTE',font=font,fill='#E8EEF5')
d.text((243,150),'LOGISTICS INTELLIGENCE',font=small,fill='#95A7B8')
img.save(A/'nexroute_logo.png')
fig,ax=plt.subplots(figsize=(15,8.3),facecolor='#0B1420')
ax.set_facecolor('#0B1420');ax.set_xlim(0,15);ax.set_ylim(0,8.3);ax.axis('off')
boxes={
 'couriers':(0.4,5.15,3.9,2.2,['Courier_ID (PK)','Assigned_Region','Courier_Name','Vehicle_Type']),
 'hubs':(0.4,1.7,3.9,2.35,['Hub_ID (PK)','Region','City','Latitude / Longitude']),
 'shipments':(5.5,2.6,4.15,4.3,['Shipment_ID (PK)','Courier_ID (FK)','Origin_Hub_ID (FK)','SLA_ID (FK)','Delivery_Status','Actual_Delivery_Date','Shipping_Cost_PHP']),
 'sla_rules':(11,5.1,3.55,2.2,['SLA_ID (PK)','Service_Type','Origin_Region','Destination_Region','SLA_Days']),
 'delivery_events':(11,1.1,3.55,2.6,['Event_ID (PK)','Shipment_ID (FK)','Event_DateTime','Event_Type','Hub_ID (FK)']),
}
for name,(x,y,w,h,fields) in boxes.items():
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06,rounding_size=.14',fc='#172738',ec='#33495D',lw=1.8))
 ax.add_patch(FancyBboxPatch((x,y+h-.56),w,.56,boxstyle='round,pad=.015,rounding_size=.1',fc='#213B51',ec='none'))
 ax.text(x+.2,y+h-.35,name.upper(),color='#2DD4BF',fontsize=12,fontweight='bold')
 for i,t in enumerate(fields):ax.text(x+.23,y+h-.91-.4*i,t,fontsize=10.2,color='#D6E1EB',fontfamily='monospace')
for start,end in [((4.3,6.2),(5.5,5.7)),((4.3,2.8),(5.5,3.4)),((9.65,5.65),(11,6.2)),((9.65,3.45),(11,2.5))]:
 ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=15,color='#4C9AFF',lw=2,connectionstyle='arc3,rad=.1'))
ax.text(.42,7.94,'NEXROUTE / RELATIONAL MODEL',fontsize=16,color='#E8EEF5',fontweight='bold')
ax.text(.42,.35,'All tables use constrained keys; each delivery event belongs to one shipment. Arrows point from references to the parent entity.',fontsize=10,color='#95A7B8')
fig.savefig(A/'database_schema.png',dpi=160,facecolor=fig.get_facecolor(),bbox_inches='tight');plt.close(fig)
