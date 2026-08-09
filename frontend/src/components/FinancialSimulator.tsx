import { useMemo, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { IdeaInput } from '../types'

interface FinancialSimulatorProps {
  idea: IdeaInput
}

const extractNumber = (text?: string, fallback = 20): number => {
  if (!text) return fallback
  const match = text.match(/[\d,]+(?:\.\d+)?/)
  return match ? Number.parseFloat(match[0].replace(/,/g, '')) : fallback
}

const money = (value: number) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0,
}).format(value)

export default function FinancialSimulator({ idea }: FinancialSimulatorProps) {
  const monthlyPrice = Math.max(1, extractNumber(idea.price, 20))
  const [cac, setCac] = useState(Math.max(10, Math.round(monthlyPrice * 3)))
  const [variableCost, setVariableCost] = useState(Math.max(1, Math.round(monthlyPrice * 0.15)))
  const [fixedCosts, setFixedCosts] = useState(500)
  const [monthlyChurn, setMonthlyChurn] = useState(5)

  const economics = useMemo(() => {
    const grossMarginPerCustomer = monthlyPrice - variableCost
    const churnRate = monthlyChurn / 100
    const replacementAcquisitionPerCustomer = churnRate * cac
    const monthlyContribution = grossMarginPerCustomer - replacementAcquisitionPerCustomer
    const breakevenCustomers = monthlyContribution > 0 ? Math.ceil(fixedCosts / monthlyContribution) : null
    const paybackMonths = grossMarginPerCustomer > 0 ? cac / grossMarginPerCustomer : null
    const estimatedLtv = churnRate > 0 && grossMarginPerCustomer > 0 ? grossMarginPerCustomer / churnRate : null
    const ltvToCac = estimatedLtv && cac > 0 ? estimatedLtv / cac : null
    return { grossMarginPerCustomer, monthlyContribution, breakevenCustomers, paybackMonths, estimatedLtv, ltvToCac }
  }, [cac, fixedCosts, monthlyChurn, monthlyPrice, variableCost])

  const chartData = useMemo(() => {
    const upperBound = Math.max(100, Math.min(1000, Math.ceil(((economics.breakevenCustomers || 100) * 2) / 25) * 25))
    const step = Math.max(10, Math.ceil(upperBound / 20 / 10) * 10)
    const points = []
    for (let customers = 0; customers <= upperBound; customers += step) {
      const revenue = customers * monthlyPrice
      const costs = fixedCosts + customers * variableCost + customers * (monthlyChurn / 100) * cac
      points.push({ customers, Revenue: Math.round(revenue), Costs: Math.round(costs) })
    }
    return points
  }, [cac, economics.breakevenCustomers, fixedCosts, monthlyChurn, monthlyPrice, variableCost])

  const health = economics.ltvToCac === null
    ? { label: 'Incomplete', className: 'text-gray-600 bg-gray-50 border-gray-200' }
    : economics.ltvToCac >= 3
    ? { label: 'Healthy', className: 'text-emerald-700 bg-emerald-50 border-emerald-200' }
    : economics.ltvToCac >= 1
    ? { label: 'Needs work', className: 'text-amber-700 bg-amber-50 border-amber-200' }
    : { label: 'Unsustainable', className: 'text-rose-700 bg-rose-50 border-rose-200' }

  return (
    <section className="verseo-card overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-200 p-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-display font-black text-gray-900">Unit economics stress test</h2>
          <p className="text-xs text-gray-500 mt-1 max-w-2xl leading-relaxed">
            A transparent subscription model using your stated monthly price of <strong>{money(monthlyPrice)}</strong>. Acquisition spend assumes you replace churned customers each month.
          </p>
        </div>
        <span className={`text-xs font-bold px-3 py-1.5 rounded-full border ${health.className}`}>{health.label}</span>
      </div>

      <div className="p-5 grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-7">
        <div className="space-y-5">
          <Slider label="Customer acquisition cost" value={cac} min={0} max={Math.max(250, monthlyPrice * 12)} step={5} suffix="$" onChange={setCac} />
          <Slider label="Variable cost / customer / month" value={variableCost} min={0} max={Math.max(50, monthlyPrice)} step={1} suffix="$" onChange={setVariableCost} />
          <Slider label="Monthly fixed costs" value={fixedCosts} min={0} max={10000} step={100} suffix="$" onChange={setFixedCosts} />
          <Slider label="Monthly churn" value={monthlyChurn} min={1} max={25} step={1} suffix="%" onChange={setMonthlyChurn} />
        </div>

        <div className="space-y-5 min-w-0">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metric label="Break-even" value={economics.breakevenCustomers ? `${economics.breakevenCustomers} customers` : 'Not reachable'} />
            <Metric label="CAC payback" value={economics.paybackMonths ? `${economics.paybackMonths.toFixed(1)} months` : 'Not reachable'} />
            <Metric label="Estimated LTV" value={economics.estimatedLtv ? money(economics.estimatedLtv) : 'Unknown'} />
            <Metric label="LTV : CAC" value={economics.ltvToCac ? `${economics.ltvToCac.toFixed(1)}×` : 'Unknown'} />
          </div>

          <div className="h-[300px] min-h-[300px]" aria-label="Monthly revenue and cost projection chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="customers" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis width={64} tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} tickFormatter={(value) => money(value)} />
                <Tooltip formatter={(value) => money(Number(value))} labelFormatter={(label) => `${label} active customers`} contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb' }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                {economics.breakevenCustomers && economics.breakevenCustomers <= chartData[chartData.length - 1].customers && (
                  <ReferenceLine x={economics.breakevenCustomers} stroke="#2563eb" strokeDasharray="4 4" label={{ value: 'Break-even', fill: '#2563eb', fontSize: 11 }} />
                )}
                <Line type="monotone" dataKey="Revenue" stroke="#059669" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="Costs" stroke="#e11d48" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[10px] text-gray-400 leading-relaxed">
            Directional model only. LTV assumes constant churn and gross margin; it excludes taxes, annual prepayment, expansion revenue, financing, and cohort effects. Validate every input with real customer data.
          </p>
        </div>
      </div>
    </section>
  )
}

function Slider({ label, value, min, max, step, suffix, onChange }: {
  label: string; value: number; min: number; max: number; step: number; suffix: '$' | '%'; onChange: (value: number) => void
}) {
  const display = suffix === '$' ? money(value) : `${value}%`
  return (
    <label className="block space-y-2">
      <span className="flex justify-between gap-3 text-xs font-semibold text-gray-700"><span>{label}</span><span className="text-blue-700 tabular-nums">{display}</span></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} className="w-full accent-blue-600" />
    </label>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-gray-50 border border-gray-200 p-3">
      <p className="text-[10px] uppercase tracking-wider font-bold text-gray-500">{label}</p>
      <p className="text-sm font-black text-gray-900 mt-1 tabular-nums">{value}</p>
    </div>
  )
}
