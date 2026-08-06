import React, { useState, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { IdeaInput } from '../types'

interface FinancialSimulatorProps {
  idea: IdeaInput
}

// Very basic helper to extract a number from a string
const extractNumber = (text?: string, defaultVal: number = 20): number => {
  if (!text) return defaultVal
  const matches = text.match(/[\d,]+(?:\.\d+)?/)
  if (matches) {
    return parseFloat(matches[0].replace(/,/g, ''))
  }
  return defaultVal
}

export const FinancialSimulator: React.FC<FinancialSimulatorProps> = ({ idea }) => {
  const basePrice = extractNumber(idea.price, 20)
  const baseBudget = extractNumber(idea.budget, 5000)

  const [cac, setCac] = useState<number>(basePrice * 2) // Default CAC is double the price initially
  const [fixedCosts, setFixedCosts] = useState<number>(500) // Default $500 monthly fixed

  const data = useMemo(() => {
    const points = []
    // Let's project from 0 to 500 customers
    for (let customers = 0; customers <= 500; customers += 25) {
      const revenue = customers * basePrice
      const totalAcquisitionCost = customers * cac
      const totalCosts = fixedCosts + totalAcquisitionCost
      const profit = revenue - totalCosts

      points.push({
        customers,
        Revenue: revenue,
        Costs: totalCosts,
        Profit: profit
      })
    }
    return points
  }, [basePrice, cac, fixedCosts])

  const breakevenCustomers = useMemo(() => {
    if (basePrice <= cac) return null // Never breakeven if CAC >= Price
    return Math.ceil(fixedCosts / (basePrice - cac))
  }, [basePrice, cac, fixedCosts])

  return (
    <div className="w-full bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm mt-6 mb-8 verseo-card">
      <div className="bg-gray-50 border-b border-gray-200 p-4 sm:p-5">
        <h3 className="text-lg font-display font-bold text-gray-900 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          Unit Economics Simulator
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Based on your stated price of <strong className="text-gray-700">${basePrice}</strong>. Adjust the CAC (Customer Acquisition Cost) to see how it affects your breakeven point.
        </p>
      </div>
      
      <div className="p-5 flex flex-col lg:flex-row gap-6">
        {/* Controls */}
        <div className="w-full lg:w-1/3 flex flex-col gap-5">
          <div className="space-y-2">
            <label className="flex justify-between text-xs font-semibold text-gray-700">
              <span>Customer Acquisition Cost (CAC)</span>
              <span className="text-blue-600">${cac}</span>
            </label>
            <input 
              type="range" 
              min="1" 
              max={basePrice * 5} 
              step="1"
              value={cac} 
              onChange={(e) => setCac(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <p className="text-[10px] text-gray-500 text-right">Cost to acquire 1 user</p>
          </div>
          
          <div className="space-y-2">
            <label className="flex justify-between text-xs font-semibold text-gray-700">
              <span>Monthly Fixed Costs</span>
              <span className="text-blue-600">${fixedCosts}</span>
            </label>
            <input 
              type="range" 
              min="0" 
              max="5000" 
              step="50"
              value={fixedCosts} 
              onChange={(e) => setFixedCosts(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <p className="text-[10px] text-gray-500 text-right">Servers, tools, etc.</p>
          </div>
          
          <div className="mt-auto pt-4 border-t border-gray-100">
            <div className="rounded-xl bg-blue-50/50 border border-blue-100 p-4">
              <span className="text-[11px] font-semibold text-blue-800 uppercase tracking-wider block mb-1">Breakeven Analysis</span>
              {breakevenCustomers ? (
                <>
                  <div className="text-2xl font-black text-blue-600">
                    {breakevenCustomers} <span className="text-sm font-medium text-blue-700">users</span>
                  </div>
                  <p className="text-xs text-blue-700/80 mt-1 leading-snug">
                    You need {breakevenCustomers} paying users to cover your fixed costs and CAC.
                  </p>
                </>
              ) : (
                <>
                  <div className="text-lg font-black text-red-500">
                    Never Profitable
                  </div>
                  <p className="text-xs text-red-700/80 mt-1 leading-snug">
                    Since CAC (${cac}) is higher than the price (${basePrice}), you lose money on every user.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full lg:w-2/3 h-[300px] min-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis 
                dataKey="customers" 
                tick={{fontSize: 11, fill: '#6b7280'}} 
                axisLine={false} 
                tickLine={false}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis 
                tick={{fontSize: 11, fill: '#6b7280'}} 
                axisLine={false} 
                tickLine={false}
                tickFormatter={(val) => `$${val}`}
              />
              <Tooltip 
                formatter={(value: any) => [`$${value}`, undefined]}
                labelFormatter={(label) => `${label} Customers`}
                contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
              {breakevenCustomers && breakevenCustomers <= 500 && (
                <ReferenceLine x={breakevenCustomers} stroke="#3b82f6" strokeDasharray="3 3" label={{ position: 'top', value: 'Breakeven', fill: '#3b82f6', fontSize: 11 }} />
              )}
              <Line type="monotone" dataKey="Revenue" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="Costs" stroke="#f43f5e" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default FinancialSimulator
