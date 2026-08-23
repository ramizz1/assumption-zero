import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { failed: boolean }

export default class AppErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    // Do not render or transmit exception details; provider responses can contain sensitive text.
  }

  render() {
    if (!this.state.failed) return this.props.children

    return (
      <main className="min-h-screen grid place-items-center bg-white px-4">
        <section role="alert" className="verseo-card max-w-lg p-8 text-center">
          <h1 className="text-xl font-black text-zinc-950">This report could not be displayed</h1>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            The saved report may use an older format. Reload once, or return home and run a new analysis.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button type="button" className="btn-primary" onClick={() => window.location.reload()}>Reload</button>
            <a className="btn-ghost" href="/">Return home</a>
          </div>
        </section>
      </main>
    )
  }
}
