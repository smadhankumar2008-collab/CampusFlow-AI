import type { Alert, AnalyticsData, DashboardData, EventForm, ParkingZone, Recommendation, Team, Zone } from './types'

const request = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; mode: string }>('/api/health'),
  dashboard: () => request<DashboardData>('/api/dashboard'),
  teams: () => request<Team[]>('/api/teams'),
  createTeam: (payload: Omit<Team, 'team_id' | 'registration_time' | 'status'>) => request<Team>('/api/teams', { method: 'POST', body: JSON.stringify(payload) }),
  checkin: (teamId: string) => request<Team>(`/api/teams/${teamId}/checkin`, { method: 'POST' }),
  zones: () => request<Zone[]>('/api/zones'),
  parking: () => request<ParkingZone[]>('/api/parking'),
  alerts: () => request<Alert[]>('/api/alerts'),
  acknowledgeAlert: (id: number) => request<Alert>(`/api/alerts/${id}/acknowledge`, { method: 'PATCH' }),
  recommendations: () => request<Recommendation[]>('/api/recommendations'),
  updateRecommendation: (id: number, status: string) => request<Recommendation>(`/api/recommendations/${id}?status=${encodeURIComponent(status)}`, { method: 'PATCH' }),
  analytics: () => request<AnalyticsData>('/api/analytics'),
  createEvent: (payload: EventForm) => request<Record<string, unknown>>('/api/events', { method: 'POST', body: JSON.stringify(payload) }),
  startSimulation: () => request<{ running: boolean; tick: number }>('/api/simulation/start', { method: 'POST' }),
  stopSimulation: () => request<{ running: boolean }>('/api/simulation/stop', { method: 'POST' }),
  tickSimulation: () => request<{ tick: number; phase: string }>('/api/simulation/tick', { method: 'POST' }),
  createReport: () => request<Record<string, unknown>>('/api/reports', { method: 'POST' }),
}
