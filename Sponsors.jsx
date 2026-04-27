function SponsorsSection() {
  const tiers = [
    { name: 'Presenting', companies: ['Anthem', 'Humana'] },
    { name: 'Platinum',   companies: ['Centene', 'Molina Healthcare', 'UnitedHealthcare', 'CVS Health'] },
    { name: 'Gold',       companies: ['Deloitte', 'Accenture', 'Optum', 'Gainwell', 'Cognosante', 'Maximus'] },
    { name: 'Silver',     companies: ['Cotiviti', 'Mathematica', 'Public Consulting Group', 'Myers and Stauffer', 'Change Healthcare', 'Kepro', 'Conduent', 'Automated Health Systems'] },
  ];
  return (
    <section className="section section--brand">
      <div className="section-inner">
        <div className="section-head">
          <div className="section-eyebrow" style={{ color: '#fff', opacity: 0.9 }}>★ Thank You</div>
          <h2 className="section-title">Sponsors &amp; Partners</h2>
          <p className="section-lead">NAMD 2026 is made possible by the organizations working alongside states to serve Medicaid enrollees.</p>
        </div>
        {tiers.map(t => (
          <div key={t.name} style={{ marginBottom: 40 }}>
            <div style={{
              fontFamily: 'var(--font-display)', fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.2em', fontSize: 13, color: '#fff', opacity: 0.9,
              borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: 10, marginBottom: 18, textAlign: 'center'
            }}>{t.name} Sponsors</div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${Math.min(t.companies.length, 4)}, 1fr)`,
              gap: 12, textAlign: 'center'
            }}>
              {t.companies.map(c => (
                <div key={c} style={{
                  padding: '22px 12px', background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.15)', borderRadius: 4,
                  fontFamily: 'var(--font-display)', fontWeight: 600, letterSpacing: '0.08em',
                  textTransform: 'uppercase', fontSize: 14, color: '#fff',
                }}>{c}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

Object.assign(window, { SponsorsSection });
