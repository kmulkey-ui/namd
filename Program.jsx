const { useState: useStateAgenda } = React;

const AGENDA = {
  'Day 1': [
    { time: '8:00 AM',  title: 'Registration & Continental Breakfast', room: 'Maryland Ballroom Foyer', tag: 'breakout' },
    { time: '9:30 AM',  title: 'Opening Plenary — State of Medicaid 2026', room: 'Potomac Ballroom', tag: 'plenary' },
    { time: '11:00 AM', title: 'Federal Briefing: CMS Priorities for FY27', room: 'Potomac Ballroom', tag: 'plenary' },
    { time: '12:30 PM', title: 'Lunch with State Delegations', room: 'Chesapeake Hall', tag: 'members' },
    { time: '2:00 PM',  title: 'Eligibility Modernization Working Group', room: 'Chesapeake 4', tag: 'members' },
    { time: '4:00 PM',  title: 'Breakout — Workforce & Provider Capacity', room: 'Woodrow Wilson A', tag: 'breakout' },
    { time: '6:30 PM',  title: 'Welcome Reception', room: 'Atrium Level', tag: 'breakout' },
  ],
  'Day 2': [
    { time: '8:30 AM',  title: 'Plenary — Medicaid at the Crossroads', room: 'Potomac Ballroom', tag: 'plenary' },
    { time: '10:15 AM', title: 'Breakout — Managed Care Contracting', room: 'Woodrow Wilson B', tag: 'breakout' },
    { time: '10:15 AM', title: 'Breakout — Behavioral Health Integration', room: 'Woodrow Wilson C', tag: 'breakout' },
    { time: '1:00 PM',  title: 'Directors-Only Roundtable', room: 'Chesapeake 4', tag: 'members' },
    { time: '3:00 PM',  title: 'Plenary — A Conversation with the CMS Administrator', room: 'Potomac Ballroom', tag: 'plenary' },
    { time: '7:00 PM',  title: 'Conference Dinner', room: 'National Harbor Waterfront', tag: 'breakout' },
  ],
  'Day 3': [
    { time: '9:00 AM',  title: 'Plenary — The Path Forward', room: 'Potomac Ballroom', tag: 'plenary' },
    { time: '10:45 AM', title: 'State Innovations Showcase', room: 'Maryland Ballroom', tag: 'breakout' },
    { time: '12:00 PM', title: 'Closing Lunch & Awards', room: 'Chesapeake Hall', tag: 'breakout' },
  ],
};

function AgendaSection() {
  const [day, setDay] = useStateAgenda('Day 1');
  return (
    <section className="section">
      <div className="section-inner">
        <div className="section-head">
          <div className="section-eyebrow">★ Program</div>
          <h2 className="section-title">Agenda</h2>
          <p className="section-lead">Three days of plenary sessions, working groups, and federal briefings.</p>
        </div>
        <div className="agenda-tabs">
          {Object.keys(AGENDA).map(d => (
            <button key={d} className={'agenda-tab ' + (d === day ? 'active' : '')} onClick={() => setDay(d)}>
              {d} · {({'Day 1':'Oct 21','Day 2':'Oct 22','Day 3':'Oct 23'})[d]}
            </button>
          ))}
        </div>
        <div>
          {AGENDA[day].map((s, i) => (
            <div className="session" key={i}>
              <div className="session-time">{s.time}</div>
              <div>
                <h4 className="session-title">{s.title}</h4>
                <div className="session-meta">{s.room}</div>
              </div>
              <div><span className={'session-tag session-tag--' + s.tag}>{s.tag}</span></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SpeakersSection() {
  const speakers = [
    { name: 'Dr. Sarah Chen',    title: 'Medicaid Director, California', initials: 'SC' },
    { name: 'Marcus Johnson',    title: 'Secretary of Health, Maryland', initials: 'MJ' },
    { name: 'Elena Rodriguez',   title: 'Administrator, CMS',            initials: 'ER' },
    { name: 'Dr. James Whitaker',title: 'Medicaid Director, Ohio',       initials: 'JW' },
    { name: 'Priya Patel',       title: 'Medicaid Director, Texas',      initials: 'PP' },
    { name: 'Robert Alvarez',    title: 'Medicaid Director, New York',   initials: 'RA' },
    { name: 'Dr. Linda Okafor',  title: 'CMCS Deputy Administrator',     initials: 'LO' },
    { name: 'Thomas Reid',       title: 'Executive Director, NAMD',      initials: 'TR' },
  ];
  return (
    <section className="section section--alt">
      <div className="section-inner">
        <div className="section-head">
          <div className="section-eyebrow">Featured Speakers</div>
          <h2 className="section-title">Leaders shaping Medicaid in 2026</h2>
        </div>
        <div className="speakers">
          {speakers.map(s => (
            <div className="speaker" key={s.name}>
              <div className="speaker-photo">{s.initials}</div>
              <div className="speaker-name">{s.name}</div>
              <div className="speaker-title">{s.title}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { AgendaSection, SpeakersSection });
