import streamlit as st
from datetime import date, datetime, timedelta
import json
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]

def api_headers(prefer=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h

def rest_get(table, params=None):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=api_headers(),
        params=params or {},
        timeout=15,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase GET failed ({r.status_code}): {r.text}")
    try:
        return r.json()
    except ValueError:
        raise RuntimeError(f"Supabase returned a non-JSON response ({r.status_code}): {r.text[:300]}")

def rest_insert(table, rows):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=api_headers("return=representation"),
        json=rows,
        timeout=15,
    )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()

def rest_delete(table, params):
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=api_headers("return=representation"),
        params=params,
        timeout=15,
    )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


st.set_page_config(page_title='Laundry Machine Booking', page_icon='🧺', layout='centered', initial_sidebar_state='collapsed')

st.markdown(r"""
<style>
:root{--red:#ff4b4b;--mint:#20bfa9;--ink:#171b24;--muted:#777;--line:#eceef2;--bg:#f5f6f8}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
header[data-testid="stHeader"]{background:transparent;height:0}.stApp{background:var(--bg)}
.block-container{max-width:470px;padding:1.2rem 1rem 5rem!important}
#MainMenu,footer{visibility:hidden}
h1,h2,h3,p{letter-spacing:-.02em}.stMarkdown h2{margin:.2rem 0 .1rem}
.phone-top{display:flex;justify-content:space-between;align-items:center;margin:4px 2px 18px}
.hello{font-size:25px;font-weight:800;color:var(--ink)}
.avatar{width:44px;height:44px;border-radius:50%;background:#ffe7df;display:grid;place-items:center;font-size:24px}
.hero{background:#fff;border-radius:26px;padding:24px 22px;box-shadow:0 10px 30px rgba(25,30,45,.08);margin:0 0 16px}
.ring{width:184px;height:184px;margin:auto;border-radius:50%;background:conic-gradient(#62d84e 0 29%,#e5e6e8 29% 100%);display:grid;place-items:center;position:relative}
.ring:after{content:"";position:absolute;width:154px;height:154px;border-radius:50%;background:white}
.ring-content{z-index:1;text-align:center}.small{font-size:13px;color:#8b8e95}
.timer{font-size:42px;font-weight:800;color:#111;line-height:1.05;margin:4px}
.washer-icon{font-size:29px;line-height:1}.machine-label{font-size:13px;color:#555}
.section-title{font-size:29px;font-weight:800;color:var(--ink);margin:4px 0}
.sub{color:#5f6672;margin-bottom:14px}
.card{background:#fff;padding:15px 16px;border-radius:19px;box-shadow:0 5px 18px rgba(25,30,45,.07);margin:10px 0}
.card-title{font-weight:850;font-size:17px;color:#171b24}
.badge{display:inline-block;background:#dffbf5;color:#008f7a;padding:6px 11px;border-radius:11px;font-weight:850}
.res-card{background:#fff;border:1px solid #e3e6eb;padding:17px 16px;border-radius:19px;box-shadow:0 5px 18px rgba(25,30,45,.07);margin:10px 0}
.res-machine{font-size:17px;font-weight:850;color:#171b24;margin-bottom:8px}
.res-date{font-size:13px;font-weight:600;color:#69717d}
.selected-note{background:#eafff9;border:1px solid #b7f2e5;border-radius:15px;padding:12px 14px;color:#137866;margin:8px 0 14px}
.limit{background:#fff;border-radius:14px;padding:10px 14px;text-align:center;color:#777;font-size:13px;margin-top:14px}
.success{text-align:center;background:#fff;border-radius:28px;padding:55px 20px;box-shadow:0 10px 30px rgba(25,30,45,.08);margin-top:40px}
.check{font-size:82px}.confirmed{font-size:31px;font-weight:900;color:#ff4b4b}
.issue{background:#fff;border-radius:20px;padding:18px;box-shadow:0 5px 18px rgba(25,30,45,.07)}
.stButton>button{width:100%;border-radius:13px;min-height:44px;font-weight:750;border:1px solid #e3e5e8;transition:.15s}
.stButton>button:hover{transform:translateY(-1px);border-color:#ff7777}
.stButton>button[kind="primary"]{background:var(--red);border-color:var(--red);color:#fff}
.stButton>button:disabled{opacity:.55;color:#6f737b;background:#eceef2}
.stDateInput>div>div{border-radius:14px}.stTextArea textarea,.stSelectbox>div>div{border-radius:14px}
.stAlert{border-radius:15px}div[data-testid="stHorizontalBlock"]{gap:.45rem}
@media(max-width:520px){.block-container{padding-left:.8rem!important;padding-right:.8rem!important}.ring{width:170px;height:170px}.ring:after{width:142px;height:142px}}

/* Force reservation machine labels to be clearly visible */
.res-card .res-machine,
.res-card .res-machine *,
.res-card .card-title,
.res-card .card-title * {
    color: #000000 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* Make login form labels clearly visible on the light page background. */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p {
    color: #111111 !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Mobile-safe seven-column calendar */
.laundry-cal-head,.laundry-cal-week{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr))!important;gap:3px!important;width:100%!important}
.laundry-cal-head div{text-align:center;color:#667085;font-size:12px;font-weight:700;padding:4px 0}
.laundry-cal-day{min-height:40px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700}
.laundry-cal-empty{min-height:40px}
.laundry-cal-available{background:#ffffff;border:2px solid #ff4b4b;color:#111827;font-weight:800;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.laundry-cal-disabled{background:#f0f1f4;color:#a8adb7}
.laundry-cal-mine{background:#dff7df;border:1px solid #9bd49b;color:#176b2c;font-weight:800}

/* Keep Streamlit calendar button rows in seven columns on phones. */
@media (max-width: 640px){
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) {
        flex-wrap: nowrap !important;
        gap: 3px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) > div[data-testid="stColumn"] {
        width: calc((100% - 18px)/7) !important;
        flex: 1 1 calc((100% - 18px)/7) !important;
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button {
        min-height: 38px !important;
        padding: 0 !important;
    }
}

.laundry-cal-link{text-decoration:none!important;box-sizing:border-box;cursor:pointer}
.laundry-cal-link:hover{background:#fff5f5!important}

/* Square cancel button beside each reservation card */
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button {
    aspect-ratio: 1 / 1 !important;
    width: 100% !important;
    min-height: 0 !important;
    padding: 0 !important;
    border-radius: 14px !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

def nav(p):
    st.session_state.page=p
    st.rerun()

def back(label,p):
    if st.button(f'‹  {label}',key=f'back-{p}'):
        # Calendar date selection uses query parameters to survive the browser
        # navigation. Clear them before going back so an old `pick` value
        # cannot immediately redirect the user forward again.
        if p == 'date':
            st.query_params.clear()
        nav(p)

def heading(title,sub=None):
    st.markdown(f'<div class="section-title">{title}</div>',unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="sub">{sub}</div>',unsafe_allow_html=True)

MACHINES={'Washer':['Washer 1','Washer 2'],'Dryer':['Dryer 1','Dryer 2']}
WASH_TIMES=[f'{h:02d}:00' for h in range(8,21)]; DRY_TIMES=[f'{h:02d}:45' for h in range(8,22)]

def student_id():
    return st.session_state.get('student_id','').strip().upper()

def user_rows():
    # Fetch by Student ID, then verify Name locally as well.
    # This avoids relying on exact REST matching behavior for the name field.
    rows = rest_get("reservations", {
        "select": "*",
        "student_id": f"eq.{student_id()}",
        "day": f"gte.{date.today().isoformat()}",
        "order": "day.asc,start_time.asc",
    })
    if not isinstance(rows, list):
        return []
    current_name = st.session_state.name.strip().casefold()
    return [
        r for r in rows
        if str(r.get("student_id","")).strip().upper() == student_id()
        and str(r.get("user_name","")).strip().casefold() == current_name
    ]

def user_count():
    return len(user_rows())

def all_upcoming_rows():
    rows = rest_get("reservations", {
        "select": "*",
        "day": f"gte.{date.today().isoformat()}",
        "order": "day.asc,start_time.asc",
    })
    return rows if isinstance(rows, list) else []

def day_bookings(day):
    rows = rest_get("reservations", {
        "select": "machine,start_time",
        "day": f"eq.{day.isoformat()}",
    })
    return {(str(r.get("machine")), str(r.get("start_time"))[:5]) for r in rows}

def slot_grid(machine,times,day,prefix,suggested=None,booked_set=None):
    booked_set = booked_set if booked_set is not None else day_bookings(day)
    cols=st.columns(4); chosen=None
    for i,t in enumerate(times):
        no=(machine,t) in booked_set
        label=('★ ' if t==suggested and not no else '')+('Booked' if no else t)
        if cols[i%4].button(label,key=f'{prefix}-{machine}-{t}',disabled=no,use_container_width=True):
            chosen=t
    return chosen

for k,v in {'page':'home','day':None,'washer':None,'wash_time':None,'dryer':None,'dry_time':None,'name':'','student_id':'','logged_in':False}.items(): st.session_state.setdefault(k,v)

# Calendar date links perform a browser navigation. Restore this lightweight
# prototype login from the query string before the login gate runs.
_q_name = st.query_params.get('u_name')
_q_sid = st.query_params.get('u_sid')
_q_pick = st.query_params.get('pick')
if _q_pick and _q_name and _q_sid and not st.session_state.logged_in:
    st.session_state.name = _q_name
    st.session_state.student_id = _q_sid.upper()
    st.session_state.logged_in = True
    st.session_state.page = 'date'

if not st.session_state.logged_in:
    heading('Laundry Machine Booking','Shared laundry booking prototype')
    name=st.text_input('Name',placeholder='e.g. Tina')
    sid=st.text_input('Student ID',placeholder='e.g. A0123456X')
    if st.button('Continue',type='primary',use_container_width=True):
        if len(name.strip()) < 2 or len(sid.strip()) < 4: st.warning('Please enter your name and Student ID.')
        else:
            st.session_state.name=name.strip(); st.session_state.student_id=sid.strip().upper(); st.session_state.logged_in=True; st.rerun()
    st.stop()

USER=st.session_state.name
page=st.session_state.page

if page=='home':
    st.markdown(f'<div class="phone-top"><div class="hello">Good Afternoon,<br>{USER}! 👋</div><div class="avatar">🧺</div></div>',unsafe_allow_html=True)
    now = datetime.now()
    active = None
    for r in user_rows():
        if r.get('machine_type') != 'Washer':
            continue
        try:
            rday = date.fromisoformat(str(r['day'])[:10])
            start = datetime.combine(rday, datetime.strptime(str(r['start_time'])[:5], '%H:%M').time())
            end = start + timedelta(hours=1)
            if start <= now < end:
                active = (r, max(0, int((end-now).total_seconds())))
                break
        except Exception:
            pass

    if active:
        r, seconds_left = active
        mm, ss = divmod(seconds_left, 60)
        st.markdown(f'''<div class="hero"><div class="ring"><div class="ring-content"><div class="small">Time Left</div><div class="timer">{mm:02d}:{ss:02d}</div><div class="washer-icon">▣</div><div class="machine-label">{r['machine']}</div></div></div></div>''',unsafe_allow_html=True)
    else:
        st.markdown('''<div class="hero" style="text-align:center;padding:34px 22px"><div style="font-size:44px">🧺</div><div class="card-title" style="margin-top:8px">No laundry in progress</div><div class="small" style="margin-top:6px">Your active washer will appear here when your reserved time begins.</div></div>''',unsafe_allow_html=True)
    if st.button('▣  Book a Timeslot',use_container_width=True,type='primary'): nav('date')
    if st.button('✓  View Reservation',use_container_width=True): nav('reservations')
    if st.button('🛠  Report an Issue',use_container_width=True): nav('issue')
    # Reservation limits are enforced by date/week rather than a raw machine-slot count.
    if st.button('Sign out',use_container_width=True):
        st.session_state.logged_in=False; st.session_state.name=''; st.session_state.student_id=''; st.rerun()

elif page=='date':
    back('Back','home')
    heading('Choose a Date','Reservations are available up to 2 weeks ahead. You can book one Washer + Dryer set per day, on up to 2 days per week.')

    my_bookings = user_rows()
    my_dates = {str(r.get('day',''))[:10] for r in my_bookings}
    my_week_dates = {}
    for r in my_bookings:
        try:
            rd = date.fromisoformat(str(r.get('day',''))[:10])
            iso = rd.isocalendar()
            my_week_dates.setdefault((iso.year, iso.week), set()).add(rd.isoformat())
        except Exception:
            pass

    def day_has_pair_capacity(check_day):
        rows = rest_get("reservations", {"select":"machine,machine_type,start_time","day":f"eq.{check_day.isoformat()}"})
        if not isinstance(rows, list): rows = []
        occupied = {(str(r.get("machine")), str(r.get("start_time"))[:5]) for r in rows}
        return (
            any((m,t) not in occupied for m in MACHINES['Washer'] for t in WASH_TIMES)
            and any((m,t) not in occupied for m in MACHINES['Dryer'] for t in DRY_TIMES)
        )

    window_start = date.today()
    window_end = window_start + timedelta(days=13)
    window_days = [window_start + timedelta(days=i) for i in range(14)]
    unavailable = set()
    for check_day in window_days:
        iso = check_day.isocalendar()
        week_limit = len(my_week_dates.get((iso.year,iso.week),set())) >= 2
        if check_day.isoformat() in my_dates or week_limit or not day_has_pair_capacity(check_day):
            unavailable.add(check_day.isoformat())

    import calendar
    import urllib.parse
    cal = calendar.Calendar(firstweekday=6)
    months = []
    cursor = date(window_start.year, window_start.month, 1)
    while (cursor.year,cursor.month) <= (window_end.year,window_end.month):
        months.append((cursor.year,cursor.month))
        cursor = date(cursor.year+1,1,1) if cursor.month==12 else date(cursor.year,cursor.month+1,1)

    # Read a directly-clicked date from the URL query string.
    picked = st.query_params.get("pick")
    if picked:
        try:
            picked_day = date.fromisoformat(picked)
            if window_start <= picked_day <= window_end and picked not in unavailable:
                st.query_params.clear()
                st.session_state.day = picked_day
                nav('washer')
        except Exception:
            st.query_params.clear()

    for year,month in months:
        st.markdown(f'<div style="font-size:17px;font-weight:800;color:#111827;margin:14px 0 8px">{calendar.month_name[month]} {year}</div>',unsafe_allow_html=True)
        html='<div class="laundry-cal-head">'+''.join(f'<div>{x}</div>' for x in ['Su','Mo','Tu','We','Th','Fr','Sa'])+'</div>'
        for week in cal.monthdatescalendar(year,month):
            html+='<div class="laundry-cal-week">'
            for day_item in week:
                kd=day_item.isoformat()
                if day_item.month!=month:
                    html+='<div class="laundry-cal-empty"></div>'
                elif kd in my_dates:
                    html+=f'<div class="laundry-cal-day laundry-cal-mine">✓ {day_item.day}</div>'
                elif not(window_start<=day_item<=window_end) or kd in unavailable:
                    html+=f'<div class="laundry-cal-day laundry-cal-disabled">{day_item.day}</div>'
                else:
                    html+=f'<a class="laundry-cal-day laundry-cal-available laundry-cal-link" href="?pick={kd}&u_name={urllib.parse.quote(USER)}&u_sid={urllib.parse.quote(student_id())}" target="_self">{day_item.day}</a>'
            html+='</div>'
        st.markdown(html,unsafe_allow_html=True)

    st.markdown('<div style="margin-top:8px;color:#667085;font-size:12px"><b>✓</b> Your reservation · Grey dates are unavailable · Outlined dates are selectable.</div>',unsafe_allow_html=True)

elif page=='washer':
    back('Back','date'); heading('Select a Washer',st.session_state.day.strftime('%A, %d %B %Y'))
    booked_set=day_bookings(st.session_state.day)
    for m in MACHINES['Washer']:
        st.markdown(f'<div class="card"><div class="card-title">▣ &nbsp;{m}</div><div class="small">1-hour blocks include buffer time</div></div>',unsafe_allow_html=True)
        t=slot_grid(m,WASH_TIMES,st.session_state.day,'wash',booked_set=booked_set)
        if t: st.session_state.washer=m; st.session_state.wash_time=t; nav('dryer')

elif page=='dryer':
    back('Back','washer'); heading('Select a Dryer',st.session_state.day.strftime('%A, %d %B %Y'))
    wash_dt=datetime.combine(st.session_state.day,datetime.strptime(st.session_state.wash_time,'%H:%M').time()); suggested=(wash_dt+timedelta(minutes=45)).strftime('%H:%M')
    st.markdown(f'<div class="selected-note">Washer selected: <b>{st.session_state.washer} · {st.session_state.wash_time}</b><br><span class="small">★ marks the suggested dryer slot after your wash cycle.</span></div>',unsafe_allow_html=True)
    booked_set=day_bookings(st.session_state.day)
    for m in MACHINES['Dryer']:
        st.markdown(f'<div class="card"><div class="card-title">♨ &nbsp;{m}</div><div class="small">Suggested around {suggested}</div></div>',unsafe_allow_html=True)
        t=slot_grid(m,DRY_TIMES,st.session_state.day,'dry',suggested,booked_set)
        if t: st.session_state.dryer=m; st.session_state.dry_time=t; nav('confirm')

elif page=='confirm':
    back('Back','dryer')
    heading('Confirm Selection',st.session_state.day.strftime('%d %B %Y'))

    def confirm_card(icon, machine, time_text):
        svg = f"""
        <svg viewBox="0 0 430 72" width="100%" height="72"
             xmlns="http://www.w3.org/2000/svg">
          <rect x="1" y="1" width="428" height="70" rx="20"
                fill="#ffffff" stroke="#e4e7ec" stroke-width="1"/>
          <text x="20" y="43" fill="#111111" font-size="17"
                font-weight="800" font-family="Arial, sans-serif">{icon}  {machine}</text>
          <rect x="350" y="16" width="62" height="40" rx="12" fill="#dffbf5"/>
          <text x="381" y="41" text-anchor="middle" fill="#007f6d"
                font-size="14" font-weight="800"
                font-family="Arial, sans-serif">{time_text}</text>
        </svg>
        """
        st.markdown(svg, unsafe_allow_html=True)

    confirm_card('▣', st.session_state.washer, st.session_state.wash_time)
    confirm_card('♨', st.session_state.dryer, st.session_state.dry_time)

    selected_day = st.session_state.day.isoformat()

    # Always query this user's reservations fresh before allowing confirmation.
    identity_rows = rest_get("reservations", {
        "select": "*",
        "student_id": f"eq.{student_id()}",
        "day": f"gte.{date.today().isoformat()}",
        "order": "day.asc,start_time.asc",
    })
    if not isinstance(identity_rows, list):
        identity_rows = []

    current_name = USER.strip().casefold()
    identity_rows = [
        r for r in identity_rows
        if str(r.get("student_id","")).strip().upper() == student_id()
        and str(r.get("user_name","")).strip().casefold() == current_name
    ]

    # A booking is a Washer + Dryer pair. If either already exists on the
    # selected date, another pair on that date is not allowed.
    same_day = [
        r for r in identity_rows
        if str(r.get("day",""))[:10] == selected_day
    ]
    daily_limit_hit = len(same_day) > 0

    # Maximum 2 distinct booking dates per ISO week (Monday-Sunday).
    selected_iso = st.session_state.day.isocalendar()
    week_dates = set()
    for r in identity_rows:
        try:
            rd = date.fromisoformat(str(r.get("day",""))[:10])
            ri = rd.isocalendar()
            if (ri.year, ri.week) == (selected_iso.year, selected_iso.week):
                week_dates.add(rd.isoformat())
        except Exception:
            pass
    weekly_limit_hit = selected_day not in week_dates and len(week_dates) >= 2

    if daily_limit_hit:
        st.error('You already have a reservation on this date. Only one Washer + Dryer booking is allowed per day.')
    elif weekly_limit_hit:
        st.error('You have reached the weekly limit of 2 reservation dates.')
    elif st.button('Confirm Reservation',use_container_width=True,type='primary'):
        try:
            rows = [
                {'student_id':student_id(),'user_name':USER,'machine':st.session_state.washer,
                 'machine_type':'Washer','day':st.session_state.day.isoformat(),
                 'start_time':st.session_state.wash_time},
                {'student_id':student_id(),'user_name':USER,'machine':st.session_state.dryer,
                 'machine_type':'Dryer','day':st.session_state.day.isoformat(),
                 'start_time':st.session_state.dry_time}
            ]
            inserted = rest_insert('reservations', rows)
            if isinstance(inserted, list) and len(inserted) == 2:
                nav('success')
            else:
                st.error('The reservation was not saved. Please try again.')
                st.caption(f'Database response: {inserted}')
        except Exception as e:
            st.error('The reservation could not be saved. The slot may have just been booked by someone else.')
            st.caption(f'Database message: {e}')

elif page=='success':
    # Keep the entire SVG in one HTML block. Blank lines inside the previous
    # multiline SVG caused Streamlit/Markdown to split the SVG after CONFIRMED!.
    success_svg = """<svg viewBox="0 0 430 360" width="100%" height="360" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="428" height="358" rx="28" fill="#ffffff"/><text x="215" y="76" text-anchor="middle" fill="#ff4b4b" font-size="28" font-weight="900" font-family="Arial, sans-serif">CONFIRMED!</text><rect x="175" y="112" width="80" height="80" rx="12" fill="#52d28a"/><path d="M194 151 L209 166 L238 137" fill="none" stroke="#ffffff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/><text x="215" y="254" text-anchor="middle" fill="#111111" font-size="22" font-weight="800" font-family="Arial, sans-serif">Your laundry timeslots are</text><text x="215" y="282" text-anchor="middle" fill="#111111" font-size="22" font-weight="800" font-family="Arial, sans-serif">reserved.</text><text x="215" y="326" text-anchor="middle" fill="#667085" font-size="13" font-weight="500" font-family="Arial, sans-serif">You can review or cancel them from View Reservation.</text></svg>"""
    st.markdown(success_svg, unsafe_allow_html=True)
    if st.button('Return Home',use_container_width=True,type='primary'): nav('home')

elif page=='reservations':
    back('Back','home')
    heading('My Reservations','Your upcoming washer and dryer bookings.')
    rows=user_rows()

    # Only show reservations whose BOTH login identifiers match.
    rows = [
        r for r in rows
        if str(r.get('student_id','')).strip().upper() == student_id()
        and str(r.get('user_name','')).strip().casefold() == USER.strip().casefold()
    ]

    if not rows:
        st.info('No upcoming reservations yet.')

    for r in rows:
        rid = r['id']
        m = r['machine']
        typ = r['machine_type']
        d = r['day']
        t = str(r['start_time'])[:5]
        icon = '▣' if typ == 'Washer' else '♨'
        date_text = datetime.fromisoformat(d).strftime("%d %b %Y")

        # Keep each reservation on one row: card on the left, square cancel
        # button on the right. The ratio remains compact on mobile.
        c1, c2 = st.columns([5.2, 1], gap="small")
        card_svg = f"""<svg viewBox="0 0 410 96" width="100%" height="96" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{m}, {date_text}, {t}"><rect x="1" y="1" width="408" height="94" rx="16" fill="#ffffff" stroke="#e4e7ec" stroke-width="1.5"/><text x="20" y="34" fill="#111111" font-size="17" font-weight="800" font-family="Arial, sans-serif">{icon}  {m}</text><text x="20" y="70" fill="#4b5563" font-size="13" font-weight="600" font-family="Arial, sans-serif">{date_text}</text><rect x="316" y="49" width="72" height="32" rx="10" fill="#dffbf5"/><text x="352" y="70" text-anchor="middle" fill="#007f6d" font-size="13" font-weight="800" font-family="Arial, sans-serif">{t}</text></svg>"""
        c1.markdown(card_svg, unsafe_allow_html=True)

        if c2.button('✕', key=f'cancel-{rid}', help='Cancel reservation', use_container_width=True):
            rest_delete(
                'reservations',
                {
                    'id': f'eq.{rid}',
                    'student_id': f'eq.{student_id()}',
                    'user_name': f'eq.{USER}'
                }
            )
            st.rerun()

elif page=='issue':
    back('Back','home'); heading('Report an Issue','Tell us what went wrong in the laundry room.')
    machine=st.selectbox('Machine',['General / Laundry room']+MACHINES['Washer']+MACHINES['Dryer']); details=st.text_area('What happened?',placeholder='e.g. Washer 2 is not draining properly...',height=140)
    if st.button('Submit Report',use_container_width=True,type='primary'):
        if not details.strip(): st.warning('Please describe the issue first.')
        else:
            rest_insert('issues', {'student_id':student_id(),'user_name':USER,'machine':machine,'details':details.strip()}); st.success('Issue reported. Thank you!')
