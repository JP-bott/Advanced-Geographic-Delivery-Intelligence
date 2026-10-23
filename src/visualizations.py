"""Consistent dark Plotly charts for the NexRoute control tower."""
import plotly.express as px
import plotly.graph_objects as go
COLORS=['#4C9AFF','#2DD4BF','#F59E0B','#EF4444','#9E8EFF','#6B8092']
BG='#111F2E'

def themed(fig,height=350):
    fig.update_layout(height=height,margin=dict(l=12,r=14,t=35,b=20),paper_bgcolor=BG,plot_bgcolor=BG,
      font=dict(family='Inter, Arial',color='#E8EEF5',size=12),colorway=COLORS,
      legend=dict(orientation='h',y=-.22),hoverlabel=dict(bgcolor='#172738',font_color='#E8EEF5'))
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor='#35475B',tickfont_color='#95A7B8')
    fig.update_yaxes(showgrid=True,gridcolor='#283A4B',zeroline=False,tickfont_color='#95A7B8')
    return fig

def empty_chart(message='No matching shipments'):
    f=go.Figure();f.add_annotation(text=message,showarrow=False,font_size=15)
    return themed(f)

def area_line(frame,x,y,title=None,rolling=None):
    if frame.empty:return empty_chart()
    f=go.Figure();f.add_trace(go.Scatter(x=frame[x],y=frame[y],fill='tozeroy',mode='lines',
      name=y,line=dict(color=COLORS[0],width=2.5),fillcolor='rgba(76,154,255,.11)'))
    if rolling and rolling in frame:
        f.add_trace(go.Scatter(x=frame[x],y=frame[rolling],mode='lines',name='Rolling mean',
         line=dict(color=COLORS[1],width=2,dash='dot')))
    f.update_layout(title=title);return themed(f)

def horizontal_bar(frame,y,x,color=COLORS[0],title=None):
    if frame.empty:return empty_chart()
    f=px.bar(frame.sort_values(x),x=x,y=y,orientation='h',title=title)
    f.update_traces(marker_color=color,marker_line_width=0)
    return themed(f,max(320,min(580,len(frame)*33+95)))

def geo_base(title='',height=480):
    f=go.Figure()
    f.update_geos(scope='asia',projection_type='mercator',showcountries=True,countrycolor='#40566B',
      showland=True,landcolor='#152638',showocean=True,oceancolor='#0B1420',
      showcoastlines=True,coastlinecolor='#38556D',
      lataxis_range=[4,21],lonaxis_range=[116,127],bgcolor=BG)
    f.update_layout(title=title,geo=dict(bgcolor=BG),dragmode='pan')
    return themed(f,height)
