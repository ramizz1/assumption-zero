export interface ReadinessCheck {
  id: string
  label: string
  hint: string
  complete: boolean
}

export interface ReadinessResult {
  score: number
  checks: ReadinessCheck[]
}

export interface IdeaDraft {
  name?: string
  description?: string
  problem?: string
  target_customer?: string
  geography?: string
  market_language?: string
  currency?: string
  industry?: string
  startup_stage?: string
  solution?: string
  business_model?: string
  price?: string
  founder_skills?: string
  team?: string
  budget?: string
  launch_timeline?: string
  revenue_goal?: string
  acquisition_channels?: string
  known_competitors?: string
  unfair_advantage?: string
  key_assumptions?: string
  regulatory_constraints?: string
  additional_context?: string
}

const resultFrom = (checks: ReadinessCheck[]): ReadinessResult => ({
  checks,
  score: Math.round((checks.filter((check) => check.complete).length / checks.length) * 100),
})

export function assessPromptReadiness(prompt: string): ReadinessResult {
  const text = prompt.trim()
  return resultFrom([
    {
      id: 'specificity', label: 'Specific idea',
      hint: 'Use at least 80 characters to explain the product clearly.',
      complete: text.length >= 80,
    },
    {
      id: 'customer', label: 'Target customer',
      hint: 'Say who experiences the problem (for example, “small law firms”).',
      complete: /\b(for|target|customer|user|buyer|team|firm|business|company|people|creator|developer|student|parent|patient)s?\b/i.test(text),
    },
    {
      id: 'problem', label: 'Pain or job',
      hint: 'Describe what is slow, expensive, risky, or frustrating today.',
      complete: /\b(problem|pain|struggl|difficult|expensive|slow|risk|cannot|can't|need|waste|manual|frustrat)/i.test(text),
    },
    {
      id: 'market', label: 'Market context',
      hint: 'Add a geography, industry, or initial niche.',
      complete: /\b(in|market|industry|sector|niche|local|global|worldwide|US|USA|UK|Europe|Asia|Africa|America)\b/i.test(text),
    },
    {
      id: 'commercial', label: 'Business evidence',
      hint: 'Add pricing, a business model, competitors, or a budget.',
      complete: /\b(price|pricing|subscription|revenue|fee|commission|sell|paid|budget|competitor|alternative|\$|€|£)/i.test(text),
    },
  ])
}

export function assessFormReadiness(idea: IdeaDraft): ReadinessResult {
  const present = (value?: string, minimum = 1) => (value?.trim().length ?? 0) >= minimum
  return resultFrom([
    {
      id: 'core', label: 'Clear product',
      hint: 'Give the idea a name and a concrete one-sentence description.',
      complete: present(idea.name, 2) && present(idea.description, 20),
    },
    {
      id: 'customer', label: 'Target customer',
      hint: 'Identify a narrow first customer segment.',
      complete: present(idea.target_customer, 5),
    },
    {
      id: 'problem', label: 'Pain or job',
      hint: 'Explain the current pain and why alternatives are inadequate.',
      complete: present(idea.problem, 30),
    },
    {
      id: 'market', label: 'Market context',
      hint: 'Choose an initial geography or market.',
      complete: present(idea.geography, 2),
    },
    {
      id: 'localization', label: 'Regional context',
      hint: 'Add the local customer language or pricing currency for deeper regional research.',
      complete: present(idea.geography, 2)
        && [idea.market_language, idea.currency, idea.regulatory_constraints]
          .some((value) => present(value, 2)),
    },
    {
      id: 'commercial', label: 'Business evidence',
      hint: 'Add at least two of pricing, model, competitors, budget, or founder fit.',
      complete: [idea.business_model, idea.price, idea.known_competitors, idea.budget, idea.founder_skills]
        .filter((value) => present(value, 2)).length >= 2,
    },
    {
      id: 'execution', label: 'Execution plan',
      hint: 'Add a stage, solution, launch goal, or acquisition channel to personalize the roadmap.',
      complete: [idea.startup_stage, idea.solution, idea.launch_timeline, idea.revenue_goal, idea.acquisition_channels]
        .filter((value) => present(value, 2)).length >= 2,
    },
  ])
}
