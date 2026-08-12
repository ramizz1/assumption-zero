import { Link } from 'react-router-dom'

const sections = [
  ['quick-start', 'Quick start'],
  ['idea-brief', 'Write a strong brief'],
  ['workflow', 'Validation workflow'],
  ['research-depth', 'Research depth'],
  ['outputs', 'Understand the report'],
  ['playbook', '30-day business playbook'],
  ['interviews', 'Customer interviews'],
  ['metrics', 'Metrics and economics'],
  ['cli', 'CLI reference'],
  ['api', 'API reference'],
  ['faq', 'FAQ'],
]

const CodeBlock = ({ children }: { children: string }) => (
  <pre className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-xs leading-6 text-zinc-200 shadow-inner"><code>{children}</code></pre>
)

const Section = ({ id, eyebrow, title, children }: { id: string; eyebrow: string; title: string; children: React.ReactNode }) => (
  <section id={id} className="scroll-mt-24 border-b border-zinc-200 pb-12 last:border-0">
    <p className="text-[10px] font-mono font-bold uppercase tracking-[0.2em] text-zinc-400 mb-2">{eyebrow}</p>
    <h2 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-zinc-950 mb-5">{title}</h2>
    <div className="space-y-5 text-sm leading-7 text-zinc-600">{children}</div>
  </section>
)

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white verseo-grid text-zinc-900 selection:bg-zinc-200">
      <header className="sticky top-0 z-30 border-b border-zinc-200 bg-white/90 backdrop-blur-xl px-4 sm:px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 hover:opacity-75 transition-opacity">
            <img src="/logo.png" alt="Assumption Zero" className="w-9 h-9 rounded-xl border border-zinc-200 object-cover" />
            <div>
              <p className="font-display font-bold leading-tight">Assumption Zero</p>
              <p className="text-[10px] font-mono text-zinc-400">FOUNDER DOCS</p>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <a href="#cli" className="btn-ghost hidden sm:inline-flex px-3 py-2 text-xs">CLI reference</a>
            <Link to="/" className="btn-primary px-4 py-2 text-xs">Analyze an idea</Link>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 lg:grid lg:grid-cols-[220px_minmax(0,1fr)] gap-12">
        <aside className="hidden lg:block">
          <nav className="sticky top-24 space-y-1" aria-label="Documentation sections">
            <p className="text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-400 px-3 mb-3">On this page</p>
            {sections.map(([id, label]) => (
              <a key={id} href={`#${id}`} className="block rounded-lg px-3 py-2 text-xs font-medium text-zinc-500 hover:text-zinc-950 hover:bg-zinc-100 transition-colors">{label}</a>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 space-y-12">
          <div className="rounded-3xl bg-zinc-950 text-white p-7 sm:p-10 overflow-hidden relative shadow-xl">
            <div className="absolute -right-12 -top-16 w-56 h-56 rounded-full border border-white/10" />
            <div className="absolute -right-2 -top-6 w-36 h-36 rounded-full border border-white/10" />
            <p className="text-[10px] font-mono font-bold tracking-[0.22em] text-zinc-400 mb-4">FROM IDEA TO EVIDENCE TO ACTION</p>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight max-w-3xl leading-[1.08]">Start a business without betting months on assumptions.</h1>
            <p className="mt-5 max-w-2xl text-zinc-300 leading-7">Use Assumption Zero to define a sharp customer problem, gather market evidence, pressure-test the economics, and leave with experiments and a 30-day operating plan.</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/" className="inline-flex rounded-xl bg-white text-zinc-950 px-4 py-2.5 text-sm font-bold hover:bg-zinc-100">Start validation</Link>
              <a href="#playbook" className="inline-flex rounded-xl border border-zinc-700 px-4 py-2.5 text-sm font-bold text-zinc-200 hover:border-zinc-500">Read the playbook</a>
            </div>
          </div>

          <Section id="quick-start" eyebrow="01 · Start here" title="Quick start">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                ['1', 'Describe the business', 'Use Prompt mode for speed or Detailed brief for control. Include the buyer, painful workflow, solution, geography, price, and constraints.'],
                ['2', 'Run the evidence engine', 'Choose Standard, Deep, or Exhaustive research. Web analyses require a validated real AI provider; the token-free example is a separate precomputed report.'],
                ['3', 'Act on thresholds', 'Use the founder roadmap and validation experiments. Pre-write success and failure thresholds before spending on a full MVP.'],
              ].map(([number, title, body]) => (
                <article key={number} className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
                  <span className="inline-grid place-items-center w-7 h-7 rounded-lg bg-zinc-950 text-white text-xs font-mono font-bold mb-3">{number}</span>
                  <h3 className="font-bold text-zinc-950 mb-1">{title}</h3>
                  <p className="text-xs leading-6">{body}</p>
                </article>
              ))}
            </div>
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950 text-xs"><strong>Important:</strong> the output is decision support, not a guarantee. Market size, legal requirements, and willingness to pay still require primary research.</div>
          </Section>

          <Section id="idea-brief" eyebrow="02 · Better input" title="Write a strong idea brief">
            <p>The best brief describes a specific situation, not a product category. “AI app for lawyers” is too broad; describe which lawyers, which repeated job, how they handle it now, and what the failure costs.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5">
                <p className="font-bold text-rose-900 mb-2">Weak</p>
                <p className="text-xs text-rose-800">An AI app that summarizes meetings for businesses.</p>
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <p className="font-bold text-emerald-900 mb-2">Strong</p>
                <p className="text-xs text-emerald-800">A $49-per-seat, on-device meeting summarizer for US law firms with 1–20 attorneys that cannot send privileged audio to cloud transcription tools.</p>
              </div>
            </div>
            <h3 className="font-bold text-zinc-950">Brief checklist</h3>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {['Narrow target customer and buying role', 'Painful current workflow and measurable cost', 'Initial geography and industry', 'Smallest proposed solution', 'Pricing and business model hypothesis', 'Founder skills, team, budget, and runway', 'Reachable acquisition channels', 'Competitors and manual alternatives', 'Launch timeline and first revenue goal', 'Legal, privacy, safety, or operational constraints'].map((item) => (
                <li key={item} className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-xs flex gap-2"><span className="text-emerald-600">✓</span>{item}</li>
              ))}
            </ul>
          </Section>

          <Section id="workflow" eyebrow="03 · How it works" title="The validation workflow">
            <ol className="space-y-3">
              {[
                ['Clarify', 'Turn the brief into an explicit customer, problem, offer, constraints, and assumptions.'],
                ['Research', 'Generate targeted competitor, demand, complaint, pricing, regulatory, and distribution queries.'],
                ['Triangulate', 'Compare market analyst, regional strategist, skeptical investor, customer researcher, and practical builder perspectives according to research depth.'],
                ['Score', 'Use deterministic weighted dimensions and evidence confidence; avoid treating eloquent AI output as proof.'],
                ['Experiment', 'Design cheap tests ordered by information value, speed, and ability to disprove the idea.'],
                ['Operate', 'Convert the result into positioning, channels, metrics, interview questions, and a 30-day roadmap.'],
              ].map(([title, body], index) => (
                <li key={title} className="flex gap-4 rounded-2xl border border-zinc-200 bg-white p-4">
                  <span className="shrink-0 font-mono font-bold text-zinc-400">{String(index + 1).padStart(2, '0')}</span>
                  <div><h3 className="font-bold text-zinc-950">{title}</h3><p className="text-xs mt-1">{body}</p></div>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="research-depth" eyebrow="03B · Control coverage" title="Choose the right research depth">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                ['Standard', '3 perspectives', 'One query per evidence category for a quick first screen.'],
                ['Deep · default', '4 perspectives', 'Two queries per category plus a regional market strategist.'],
                ['Exhaustive', '5 perspectives', 'Up to four queries per category plus regional and customer-research specialists.'],
              ].map(([title, count, body]) => (
                <article key={title} className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
                  <h3 className="font-bold text-zinc-950">{title}</h3>
                  <p className="mt-1 text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700">{count}</p>
                  <p className="mt-3 text-xs">{body}</p>
                </article>
              ))}
            </div>
            <p>Exhaustive mode performs more searches and model calls, so it can take longer and consume more API quota. It does not make weak evidence certain: important regional claims still need citations and local customer interviews.</p>
            <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5">
              <h3 className="font-bold text-zinc-950">Regional analysis is separate and conservative</h3>
              <p className="mt-2 text-xs">Only evidence tied to the selected geography contributes to the regional evidence score. The report separates demand, pricing, regulation, and distribution; shows source and evidence coverage; and gives a localization checklist plus unresolved research gaps.</p>
            </div>
          </Section>

          <Section id="outputs" eyebrow="04 · Read the result" title="Understand the report">
            <div className="overflow-x-auto rounded-2xl border border-zinc-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-100 text-zinc-950"><tr><th className="p-3">Output</th><th className="p-3">Use it for</th><th className="p-3">Do not treat it as</th></tr></thead>
                <tbody className="divide-y divide-zinc-200">
                  {[
                    ['Opportunity score', 'Comparing evidence-backed dimensions', 'A probability of success'],
                    ['Evidence confidence', 'Judging how much research supports the analysis', 'Proof that every claim is true'],
                    ['Regional market reality', 'Checking local demand, price, rules, channels, and evidence gaps', 'A probability that the business succeeds locally'],
                    ['Competitor intelligence', 'Finding alternatives, complaints, and differentiation hypotheses', 'A complete market map'],
                    ['Unit economics', 'Stress-testing price, CAC, costs, churn, and break-even', 'A financial forecast'],
                    ['Founder toolkit', 'Planning interviews, channels, metrics, and decision gates', 'A fixed strategy'],
                    ['Experiments', 'Learning before expensive development', 'Permission to collect money deceptively'],
                  ].map((row) => <tr key={row[0]} className="bg-white"><th className="p-3 font-bold text-zinc-900">{row[0]}</th><td className="p-3">{row[1]}</td><td className="p-3 text-zinc-500">{row[2]}</td></tr>)}
                </tbody>
              </table>
            </div>
          </Section>

          <Section id="playbook" eyebrow="05 · Execute" title="A practical 30-day business playbook">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                ['Days 1–3', 'Recruit', 'Build a list of 30 qualified prospects, write a neutral interview script, and schedule ten calls.', 'Exit: 10 interviews booked'],
                ['Days 4–10', 'Discover', 'Ask about the last real occurrence, current workaround, frequency, cost, urgency, and buying authority.', 'Exit: 7/10 confirm an urgent pain'],
                ['Days 11–20', 'Test commitment', 'Deliver the core outcome manually and ask for money, a deposit, pilot agreement, or scheduled onboarding.', 'Exit: 3 meaningful commitments'],
                ['Days 21–30', 'Pilot', 'Build only the narrowest core value loop. Measure activation, time-to-value, repeat use, and willingness to continue.', 'Exit: repeat use and a paid path'],
              ].map(([phase, title, body, exit]) => (
                <article key={phase} className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
                  <p className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-wider">{phase}</p>
                  <h3 className="font-bold text-zinc-950 text-lg mt-1">{title}</h3>
                  <p className="text-xs mt-2">{body}</p>
                  <p className="text-xs font-semibold text-emerald-800 bg-emerald-50 rounded-lg p-2 mt-4">{exit}</p>
                </article>
              ))}
            </div>
          </Section>

          <Section id="interviews" eyebrow="06 · Primary evidence" title="Customer interview rules">
            <ul className="space-y-2">
              {['Ask about the last real event, not what someone might do in the future.', 'Do not pitch until you understand the current workflow and consequences.', 'Ask what they already pay in money, time, risk, or lost revenue.', 'Separate the user, champion, budget owner, and final decision maker.', 'Treat compliments as weak evidence; commitments of time, access, reputation, or money are stronger.', 'Write the pass/fail threshold before reviewing responses.'].map((rule) => <li key={rule} className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-xs flex gap-3"><span className="font-mono text-zinc-400">→</span>{rule}</li>)}
            </ul>
            <div className="rounded-2xl bg-zinc-950 text-zinc-200 p-5 text-xs leading-6"><strong className="text-white">Useful opener:</strong> “I am researching how people handle this problem. I am not selling anything today. Could you walk me through the last time it happened?”</div>
          </Section>

          <Section id="metrics" eyebrow="07 · Measure reality" title="Metrics and unit economics">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                ['Activation', 'Percent of new users who complete the core value loop.'],
                ['Time to value', 'Minutes or days until the customer receives the promised outcome.'],
                ['Retention', 'Percent who repeat the core behavior after four weeks.'],
                ['CAC', 'Sales and marketing cost divided by new paying customers.'],
                ['Gross profit', 'Revenue minus variable delivery and support costs.'],
                ['CAC payback', 'Months of gross profit required to recover acquisition cost.'],
              ].map(([metric, definition]) => <div key={metric} className="rounded-2xl border border-zinc-200 bg-white p-4"><h3 className="font-bold text-zinc-950">{metric}</h3><p className="text-xs mt-1">{definition}</p></div>)}
            </div>
            <p>Use the report’s simulator to vary price, acquisition cost, monthly service cost, fixed cost, and churn. A model is useful when it reveals which assumption controls the outcome—not when it produces a precise-looking number.</p>
          </Section>

          <Section id="cli" eyebrow="08 · Terminal" title="CLI reference">
            <CodeBlock>{`# Interactive founder brief
azero analyze

# One-prompt validation
azero prompt "A $49/month privacy-first meeting tool for small US law firms..." --depth deep

# Analyze a structured JSON brief
azero analyze --file examples/sample-idea.json --depth exhaustive

# Add local market context
azero analyze --geography Azerbaijan --language Azerbaijani --currency AZN

# Choose providers and research sources
azero analyze --provider ollama --research-provider Wikipedia --research-provider GitHub

# Review and export saved work
azero list
azero show <analysis-id>
azero export <analysis-id> --format markdown
azero export <analysis-id> --format json
azero export <analysis-id> --format html

# Stress-test unit economics
azero simulate <analysis-id>

# Provider setup and web app
azero config
azero verify-provider
azero serve`}</CodeBlock>
            <p>Run <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-900">azero --help</code> or <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-900">azero COMMAND --help</code> for every option.</p>
          </Section>

          <Section id="api" eyebrow="09 · Integrate" title="API reference">
            <CodeBlock>{`# Health and configured providers
GET /api/health

# Start from structured data
POST /api/analyses
{ "idea": { "name": "...", "description": "...", "problem": "...",
  "target_customer": "...", "geography": "...", "market_language": "...",
  "currency": "..." }, "research_depth": "deep" }

# Start from a natural-language brief
POST /api/analyses/from-prompt
{ "prompt": "A detailed startup brief...", "research_depth": "exhaustive" }

# Poll, list, or delete analyses
GET /api/analyses/{id}
GET /api/analyses?search=&status=&limit=20
DELETE /api/analyses/{id}`}</CodeBlock>
            <p>The interactive OpenAPI explorer is available at <a href="/docs" className="font-semibold text-zinc-950 underline">the backend <code>/docs</code> endpoint</a> when the API server is running separately. In the web app, this founder guide owns the same route, so use the backend port directly for OpenAPI.</p>
          </Section>

          <Section id="faq" eyebrow="10 · Common questions" title="FAQ">
            <div className="space-y-3">
              {[
                ['Should I build when the recommendation says Build?', 'Only the narrowest value loop supported by evidence. Keep interviewing and require real usage or payment milestones.'],
                ['What if evidence confidence is low?', 'Treat the report as a research queue. Run interviews, pricing tests, and source-specific searches before making an expensive decision.'],
                ['Does the example consume AI credits?', 'No. The example is a precomputed, source-backed report. Your own web analysis requires a validated AI provider and never silently falls back to mock output.'],
                ['Are market sizes and competitor claims guaranteed?', 'No. Open every citation, check its date and scope, and verify important claims with primary sources.'],
                ['What should I do first?', 'Recruit ten narrowly matched customer interviews. Do that before naming features, choosing architecture, or buying ads.'],
              ].map(([question, answer]) => <details key={question} className="group rounded-2xl border border-zinc-200 bg-white p-4"><summary className="cursor-pointer font-bold text-zinc-950 list-none flex justify-between gap-4">{question}<span className="text-zinc-400 group-open:rotate-45 transition-transform">+</span></summary><p className="text-xs mt-3 pr-8">{answer}</p></details>)}
            </div>
          </Section>

          <div className="rounded-3xl border border-zinc-200 bg-zinc-50 p-7 text-center">
            <h2 className="font-display text-2xl font-black text-zinc-950">Ready to test the assumption?</h2>
            <p className="text-sm text-zinc-500 mt-2 mb-5">Bring a specific customer problem. Leave with measurable next actions.</p>
            <Link to="/" className="btn-primary inline-flex px-5 py-3">Start a new analysis</Link>
          </div>
        </main>
      </div>
    </div>
  )
}
