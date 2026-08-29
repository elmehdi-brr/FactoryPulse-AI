export function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div>
          <span className="brand-mark">FP</span>
          <span className="brand-name">FactoryPulse AI</span>
        </div>

        <span className="app-status">Frontend Foundation</span>
      </header>

      <main className="app-main">
        <section className="hero">
          <p className="eyebrow">Industrial Intelligence Platform</p>

          <h1>
            Factory operations,
            <br />
            understood clearly.
          </h1>

          <p className="hero-description">
            Production, reliability, maintenance, alerts, and operational
            intelligence in one system.
          </p>

          <div className="foundation-grid">
            <article className="foundation-card">
              <span>01</span>
              <h2>Production</h2>
              <p>OEE, production runs, downtime, and performance.</p>
            </article>

            <article className="foundation-card">
              <span>02</span>
              <h2>Reliability</h2>
              <p>Failure analysis, MTTR, MTBF, and machine health.</p>
            </article>

            <article className="foundation-card">
              <span>03</span>
              <h2>Intelligence</h2>
              <p>Operational priorities, causes, and performance trends.</p>
            </article>
          </div>
        </section>
      </main>
    </div>
  )
}