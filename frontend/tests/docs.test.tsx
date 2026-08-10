import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import DocsPage from '../src/pages/DocsPage'

describe('founder documentation', () => {
  it('renders the business playbook and tool references', () => {
    render(<MemoryRouter><DocsPage /></MemoryRouter>)

    expect(screen.getByRole('heading', { name: /start a business without betting months/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /30-day business playbook/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /CLI reference/i })).toBeInTheDocument()
    expect(screen.getByText(/10 interviews booked/i)).toBeInTheDocument()
  })
})
