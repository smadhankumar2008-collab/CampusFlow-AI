export type PageKey =
  | 'overview'
  | 'events'
  | 'registration'
  | 'checkin'
  | 'monitoring'
  | 'parking'
  | 'map'
  | 'alerts'
  | 'recommendations'
  | 'analytics'
  | 'reports'
  | 'settings'

export type Severity = 'SAFE' | 'CAUTION' | 'WARNING' | 'CRITICAL'

export interface Team {
  id?: number
  team_id: string
  team_name: string
  institution: string
  department: string
  leader: string
  phone: string
  members: number
  category: string
  registration_time: string
  arrival_time?: string | null
  checkin_time?: string | null
  counter?: string | null
  status: 'REGISTERED' | 'ARRIVED' | 'CHECKED-IN' | 'COMPLETED'
}

export interface Zone {
  id: string
  name: string
  capacity: number
  people_count: number
  occupancy: number
  entry_rate: number
  exit_rate: number
  growth_rate: number
  risk_score: number
  status: Severity
}

export interface ParkingZone {
  id: string
  name: string
  capacity: number
  vehicle_count: number
  occupancy: number
  entry_rate: number
  exit_rate: number
  growth_rate: number
  predicted_full_time?: number | null
  risk_level: Severity
}

export interface Alert {
  id: number
  created_at: string
  severity: Severity
  alert_type: string
  location: string
  title: string
  detail: string
  prediction?: string | null
  recommendation?: string | null
  acknowledged: number
}

export interface Recommendation {
  id: number
  created_at: string
  severity: Severity
  location: string
  problem: string
  evidence: string
  prediction: string
  action: string
  status: string
}

export interface DashboardData {
  event: {
    event_id: string
    name: string
    venue: string
    date: string
    status: string
  }
  teams: Record<string, { count: number; members: number }>
  participants: number
  queue: number
  parking_occupancy: number
  overall_risk: number
  risk_label: Severity
  active_alerts: number
  open_recommendations: number
}

export interface AnalyticsData {
  crowd: Array<{ time: string; actual: number; predicted: number }>
  parking: Array<{ time: string; actual: number }>
  registration: Array<{ time: string; teams: number }>
  metrics: {
    total_participants: number
    total_teams: number
    teams_arrived: number
    teams_checked_in: number
    peak_crowd: number
    peak_parking: number
    avg_registration: number
    avg_wait: number
    total_alerts: number
    critical_alerts: number
  }
}

export interface EventForm {
  name: string
  event_type: string
  venue: string
  event_date: string
  start_time: string
  end_time: string
  expected_participants: number
  expected_teams: number
  registration_counters: number
  parking_zones: number
  parking_capacity: number
}
