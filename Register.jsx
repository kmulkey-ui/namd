const { useState: useStateReg } = React;

const TIERS = [
  { id: 'director', name: 'State Medicaid Director', desc: 'Complimentary for current directors and deputies',    price: '$0' },
  { id: 'member',   name: 'NAMD Member',             desc: 'State and territorial Medicaid agency staff',          price: '$795' },
  { id: 'federal',  name: 'Federal Partner',         desc: 'CMS, HHS, OMB, and other federal government employees', price: '$895' },
  { id: 'industry', name: 'Industry & Non-Member',   desc: 'Plans, vendors, providers, consultants',                price: '$1,895' },
];

function RegisterSection() {
  const [tier, setTier] = useStateReg('director');
  const [submitted, setSubmitted] = useStateReg(false);

  if (submitted) {
    return (
      <section className="section">
        <div className="section-inner">
          <div className="form-card" style={{ textAlign: 'center' }}>
            <div className="section-eyebrow" style={{ marginBottom: 16 }}>★ Confirmed</div>
            <h2 className="section-title" style={{ fontSize: 32 }}>Registration received.</h2>
            <hr className="rule-red" style={{ maxWidth: 120, margin: '20px auto' }} />
            <p style={{ color: 'var(--fg-2)', fontSize: 15, lineHeight: 1.6 }}>
              A confirmation has been sent to your email. We look forward to seeing you at National Harbor, October 21–23, 2026.
            </p>
            <button className="btn btn--secondary" onClick={() => setSubmitted(false)} style={{ marginTop: 24 }}>Register Another</button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="section">
      <div className="section-inner">
        <div className="section-head">
          <div className="section-eyebrow">Registration</div>
          <h2 className="section-title">Reserve your seat</h2>
          <p className="section-lead">Registration for NAMD 2026 is now open.</p>
        </div>
        <form className="form-card" onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}>
          <div className="form-row">
            <div><label className="form-label">First Name</label><input className="form-input" required defaultValue="Jane" /></div>
            <div><label className="form-label">Last Name</label><input className="form-input" required defaultValue="Director" /></div>
          </div>
          <div className="form-row">
            <div><label className="form-label">Email</label><input className="form-input" type="email" required defaultValue="jane.director@state.gov" /></div>
            <div><label className="form-label">State / Organization</label><input className="form-input" required defaultValue="Maryland DHMH" /></div>
          </div>
          <div className="form-row form-row--single">
            <div><label className="form-label">Title</label><input className="form-input" defaultValue="Deputy Medicaid Director" /></div>
          </div>

          <label className="form-label" style={{ marginTop: 8 }}>Registration Tier</label>
          <div className="form-tiers">
            {TIERS.map(t => (
              <label key={t.id} className={'form-tier ' + (tier === t.id ? 'form-tier--active' : '')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <input type="radio" name="tier" checked={tier === t.id} onChange={() => setTier(t.id)} />
                  <div>
                    <div className="form-tier-name">{t.name}</div>
                    <div className="form-tier-desc">{t.desc}</div>
                  </div>
                </div>
                <div className="form-tier-price">{t.price}</div>
              </label>
            ))}
          </div>

          <hr className="rule-red" />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
            <div style={{ fontSize: 12, color: 'var(--fg-3)' }}>By registering you agree to the <a href="#">Code of Conduct</a>.</div>
            <button type="submit" className="btn btn--primary">Complete Registration</button>
          </div>
        </form>
      </div>
    </section>
  );
}

Object.assign(window, { RegisterSection });
