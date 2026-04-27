const { useState: useStateHero } = React;

function Hero({ onRegister }) {
  // Hero imagery is pre-composited with the NAMD 2026 lockup, so the photo
  // stands alone (no overlay text). The dark-blue band below carries the
  // date/location lockup and CTAs.
  return (
    <section className="hero" aria-label="NAMD 2026 Fall Conference">
      <div className="hero-photo" role="img"
           aria-label="NAMD 2026 Fall Conference lockup over the Gaylord National Resort atrium"
           style={{ backgroundImage: "url('../../assets/hero-mobile-1.png')" }} />
      <div className="hero-band">
        <div className="hero-eyebrow">The 2026 Fall Conference</div>
        <div><div className="hero-meta">
          October 21–23, 2026 <span className="star">★</span> National Harbor, Maryland
        </div></div>
        <div className="hero-cta">
          <button className="btn btn--on-dark" onClick={onRegister}>Register Now</button>
          <button className="btn btn--secondary" style={{ color: '#fff', borderColor: '#fff' }}>View Agenda</button>
        </div>
      </div>
    </section>
  );
}

function StatsBar() {
  const stats = [
    { num: '56', label: 'State & Territorial Agencies' },
    { num: '80M+', label: 'Medicaid Enrollees Represented' },
    { num: '1,400', label: 'Expected Attendees' },
    { num: '3', label: 'Days at National Harbor' },
  ];
  return (
    <section className="section section--alt">
      <div className="section-inner">
        <div className="stats">
          {stats.map(s => (
            <div key={s.label}>
              <div className="stat-num">{s.num}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AboutSection() {
  return (
    <section className="section">
      <div className="section-inner">
        <div className="section-head">
          <div className="section-eyebrow">About the Conference</div>
          <h2 className="section-title">Three days on the Potomac.<br/>One national conversation.</h2>
          <p className="section-lead">
            NAMD 2026 convenes state Medicaid directors, federal officials, plan
            leaders, providers, and policy experts for plenary sessions, closed
            working groups, and federal briefings at the Gaylord National Resort.
          </p>
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { Hero, StatsBar, AboutSection });
