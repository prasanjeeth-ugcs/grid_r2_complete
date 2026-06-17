import pandas as pd, numpy as np, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
df = pd.read_csv(r'd:\round2 - anti\Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv', low_memory=False)
df.replace('NULL', np.nan, inplace=True)
df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce', utc=True)
df['hour_of_day'] = df['start_datetime'].dt.hour
for c in ['event_cause','corridor','veh_type']:
    df[c] = df[c].astype(str).str.strip().replace('nan', np.nan)

# A: Corridor x Hour peaks
ct = pd.crosstab(df['corridor'], df['hour_of_day'])
top15 = df['corridor'].value_counts().head(15).index
print("=== A: CORRIDOR PEAK HOURS ===")
for corr in top15:
    row = ct.loc[corr]
    peak = int(row.idxmax())
    ist = (peak+5)%24
    print(f"  {corr:28s} Peak UTC {peak:02d}:00 (IST ~{ist:02d}:30) = {int(row.max())} events, total={int(row.sum())}")

print("\n=== B: CAUSE PEAK HOURS ===")
ct2 = pd.crosstab(df['event_cause'], df['hour_of_day'])
for cause in df['event_cause'].value_counts().head(12).index:
    row = ct2.loc[cause]
    peak = int(row.idxmax())
    ist = (peak+5)%24
    top3 = row.nlargest(3)
    t3 = " | ".join([f"UTC {int(h):02d}={int(v)}" for h,v in top3.items()])
    print(f"  {cause:25s} Peak IST ~{ist:02d}:30 | Top3: {t3}")

bd = df[df['event_cause']=='vehicle_breakdown']
night_hrs = list(range(18,24)) + list(range(0,6))
night = bd[bd['hour_of_day'].isin(night_hrs)]
day = bd[~bd['hour_of_day'].isin(night_hrs)]
print(f"\n  BREAKDOWN Night(IST 23:30-11:30): {len(night)} ({len(night)/len(bd)*100:.1f}%)")
print(f"  BREAKDOWN Day(IST 11:30-23:30):   {len(day)} ({len(day)/len(bd)*100:.1f}%)")

wl = df[df['event_cause']=='water_logging']
wl_m = wl['start_datetime'].dt.month.value_counts().sort_index()
mn = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',11:'Nov',12:'Dec'}
print("\n  WATER LOGGING by month:")
for m,c in wl_m.items():
    print(f"    {mn.get(int(m),str(m)):5s}: {int(c)} events")

print("\n=== C: CLOSURE RATE BY CORRIDOR ===")
df['requires_road_closure'] = df['requires_road_closure'].map({True:True,False:False,'TRUE':True,'FALSE':False})
cl = df.groupby('corridor')['requires_road_closure'].agg(['mean','sum','count']).reset_index()
cl.columns = ['Corridor','Rate','Closures','Total']
cl['Rate'] = (cl['Rate']*100).round(1)
cl = cl.sort_values('Rate', ascending=False)
for _,r in cl.iterrows():
    c = r['Corridor']
    rt = r['Rate']
    cls = int(r['Closures'])
    tot = int(r['Total'])
    print(f"  {c:28s} {rt:>6.1f}% ({cls}/{tot})")
