const { useState } = React;

// ===== Top bar =====
function TopBar() {
  return (
    <div className="topbar">
      <div className="topbar-inner">
        <div>Oct 21–23, 2026 <span className="topbar-sep">★</span> National Harbor, MD</div>
        <div>
          <a href="#">Members Portal</a>
          <span className="topbar-sep">·</span>
          <a href="#">Press</a>
          <span className="topbar-sep">·</span>
          <a href="#">Contact</a>
        </div>
      </div>
    </div>
  );
}

// ===== Site header with nav =====
function SiteHeader({ current, onNav }) {
  const items = ['Overview', 'Agenda', 'Speakers', 'Register', 'Sponsors'];
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a href="#" className="site-logo" onClick={(e) => { e.preventDefault(); onNav('Overview'); }}>
          <img src="../../assets/logo-horiz-nodates.png" alt="NAMD 2026 Fall Conference" />
        </a>
        <nav className="site-nav">
          {items.map(i => (
            <a key={i} href="#"
               className={current === i ? 'active' : ''}
               onClick={(e) => { e.preventDefault(); onNav(i); }}>
              {i}
            </a>
          ))}
          <button className="btn btn--red" onClick={() => onNav('Register')}>Register</button>
        </nav>
      </div>
    </header>
  );
}

// ===== Footer =====
function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-logo">
          <img src="../../assets/logo-horiz-full.png" alt="NAMD 2026" />
          <div style={{ fontSize: 12, opacity: 0.85, lineHeight: 1.6 }}>
            The annual gathering of the nation's Medicaid leadership.<br/>
            Hosted by the National Association of Medicaid Directors.
          </div>
        </div>
        <div className="footer-col">
          <h4>Conference</h4>
          <a href="#">Overview</a>
          <a href="#">Agenda</a>
          <a href="#">Speakers</a>
          <a href="#">Venue</a>
          <a href="#">Travel</a>
        </div>
        <div className="footer-col">
          <h4>Attend</h4>
          <a href="#">Register</a>
          <a href="#">Group Rates</a>
          <a href="#">Scholarships</a>
          <a href="#">Code of Conduct</a>
        </div>
        <div className="footer-col">
          <h4>NAMD</h4>
          <a href="#">About</a>
          <a href="#">Publications</a>
          <a href="#">Policy Briefs</a>
          <a href="#">Contact</a>
        </div>
      </div>
      <div className="footer-bottom">
        <div>© 2026 National Association of Medicaid Directors</div>
        <div>Washington, D.C.</div>
      </div>
    </footer>
  );
}

Object.assign(window, { TopBar, SiteHeader, SiteFooter });
