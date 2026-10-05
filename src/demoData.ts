import type { Alert, AnalyticsData, DashboardData, ParkingZone, Recommendation, Team, Zone } from './types'

const now = new Date()
const minutesAgo = (minutes: number) => new Date(now.getTime() - minutes * 60_000).toISOString()

export const demoDashboard: DashboardData = {
  event: { event_id: 'CF-KCE-2026', name: 'KCE Tech Fest 2026', venue: 'Kumaraguru College of Engineering', date: '18 Oct 2026', status: 'LIVE' },
  teams: {
    REGISTERED: { count: 9, members: 66 },
    ARRIVED: { count: 7, members: 42 },
    'CHECKED-IN': { count: 34, members: 1176 },
    COMPLETED: { count: 0, members: 0 },
  },
  participants: 1284,
  queue: 18,
  parking_occupancy: 91,
  overall_risk: 68,
  risk_label: 'WARNING',
  active_alerts: 4,
  open_recommendations: 3,
}

export const demoZones: Zone[] = [
  { id: 'main-stage', name: 'Main Stage', capacity: 520, people_count: 438, occupancy: 84.2, entry_rate: 18.3, exit_rate: 5.2, growth_rate: 13.1, risk_score: 67, status: 'WARNING' },
  { id: 'registration', name: 'Registration', capacity: 160, people_count: 132, occupancy: 82.5, entry_rate: 14.2, exit_rate: 4.5, growth_rate: 9.7, risk_score: 62, status: 'WARNING' },
  { id: 'food-court', name: 'Food Court', capacity: 260, people_count: 174, occupancy: 66.9, entry_rate: 8.4, exit_rate: 4.8, growth_rate: 3.6, risk_score: 44, status: 'CAUTION' },
  { id: 'activities', name: 'Activities', capacity: 330, people_count: 188, occupancy: 57, entry_rate: 7.8, exit_rate: 4.9, growth_rate: 2.9, risk_score: 37, status: 'CAUTION' },
  { id: 'entry', name: 'Entry Gate', capacity: 180, people_count: 78, occupancy: 43.3, entry_rate: 10.8, exit_rate: 8.2, growth_rate: 2.6, risk_score: 28, status: 'SAFE' },
  { id: 'exit', name: 'Exit Gate', capacity: 140, people_count: 44, occupancy: 31.4, entry_rate: 3.7, exit_rate: 6.4, growth_rate: -2.7, risk_score: 18, status: 'SAFE' },
]

export const demoParking: ParkingZone[] = [
  { id: 'parking-a', name: 'Parking A', capacity: 180, vehicle_count: 169, occupancy: 93.9, entry_rate: 12, exit_rate: 2.7, growth_rate: 9.3, predicted_full_time: 8, risk_level: 'CRITICAL' },
  { id: 'parking-b', name: 'Parking B', capacity: 120, vehicle_count: 54, occupancy: 45, entry_rate: 4.4, exit_rate: 2.7, growth_rate: 1.7, predicted_full_time: 39, risk_level: 'CAUTION' },
  { id: 'two-wheeler', name: 'Two-Wheeler Parking', capacity: 300, vehicle_count: 278, occupancy: 92.6, entry_rate: 10.2, exit_rate: 3.3, growth_rate: 6.9, predicted_full_time: 3, risk_level: 'CRITICAL' },
  { id: 'vip', name: 'VIP Parking', capacity: 45, vehicle_count: 25, occupancy: 55.6, entry_rate: 1.8, exit_rate: 0.9, growth_rate: 0.9, predicted_full_time: 22, risk_level: 'CAUTION' },
]

export const demoTeams: Team[] = Array.from({ length: 12 }, (_, index) => {
  const statuses: Team['status'][] = ['CHECKED-IN', 'CHECKED-IN', 'CHECKED-IN', 'ARRIVED', 'REGISTERED']
  const status = statuses[index % statuses.length]
  return {
    id: index + 1,
    team_id: `CF26-${String(index + 1).padStart(3, '0')}`,
    team_name: ['Circuit Breakers', 'Pixel Pioneers', 'Neural Navigators', 'Byte Brigade', 'The Debuggers', 'Code Catalysts'][index % 6] + ` ${String(index + 1).padStart(2, '0')}`,
    institution: ['KCE', 'PSG Tech', 'Amrita Vishwa Vidyapeetham', 'CIT Coimbatore'][index % 4],
    department: ['CSE', 'ECE', 'AI & DS', 'IT'][index % 4],
    leader: `Team Lead ${String(index + 1).padStart(2, '0')}`,
    phone: '+91 98 7000 00' + String(index + 1).padStart(2, '0'),
    members: 3 + (index % 5),
    category: ['Hackathon', 'Robo Race', 'Paper Presentation', 'UI Sprint'][index % 4],
    registration_time: minutesAgo(75 - index * 3),
    arrival_time: status === 'REGISTERED' ? null : minutesAgo(58 - index * 2),
    checkin_time: status === 'CHECKED-IN' ? minutesAgo(52 - index * 2) : null,
    counter: status === 'REGISTERED' ? null : `Counter ${(index % 3) + 1}`,
    status,
  }
})

export const demoAlerts: Alert[] = [
  { id: 1, created_at: minutesAgo(2), severity: 'CRITICAL', alert_type: 'Parking Alert', location: 'Parking A', title: 'Parking A is nearing capacity', detail: '98% occupancy with arrivals outpacing exits.', prediction: 'Full in approximately 4 minutes.', recommendation: 'Redirect incoming vehicles to Parking B.', acknowledged: 0 },
  { id: 2, created_at: minutesAgo(7), severity: 'WARNING', alert_type: 'Registration Alert', location: 'Counter 1', title: 'Registration queue is growing', detail: '18 teams are waiting; utilization is at 91%.', prediction: 'Congestion predicted in 3 minutes.', recommendation: 'Open Counter 3 and redirect incoming teams.', acknowledged: 0 },
  { id: 3, created_at: minutesAgo(12), severity: 'CAUTION', alert_type: 'Crowd Alert', location: 'Main Stage', title: 'Main Stage density is rising', detail: 'Occupancy crossed 78% with +13 people/min growth.', prediction: 'Peak crowd expected in 18 minutes.', recommendation: 'Use the north route for stage entry.', acknowledged: 0 },
  { id: 4, created_at: minutesAgo(19), severity: 'CAUTION', alert_type: 'Bottleneck Alert', location: 'Food Court', title: 'Food Court queue is building', detail: 'Queue length increased for 5 consecutive readings.', prediction: 'Service queue may exceed safe wait time.', recommendation: 'Open the secondary service queue.', acknowledged: 0 },
]

export const demoRecommendations: Recommendation[] = [
  { id: 1, created_at: minutesAgo(5), severity: 'WARNING', location: 'Counter 1', problem: 'Registration counter 1 queue is growing rapidly.', evidence: '18 teams waiting · 91% utilization · +4 teams/min', prediction: 'Counter 1 may become congested in approximately 3 minutes.', action: 'Open Counter 3 and redirect incoming teams.', status: 'OPEN' },
  { id: 2, created_at: minutesAgo(8), severity: 'CRITICAL', location: 'Parking A', problem: 'Parking A is approaching capacity.', evidence: '94% occupied · +12 vehicles/min · 11 spaces remaining', prediction: 'Parking A may reach full capacity in approximately 8 minutes.', action: 'Redirect incoming vehicles to Parking B.', status: 'OPEN' },
  { id: 3, created_at: minutesAgo(14), severity: 'CAUTION', location: 'Main Stage', problem: 'Main Stage crowd is increasing rapidly.', evidence: '82% occupied · +13 people/min · entry flow is concentrated', prediction: 'Stage zone may become critical during the next arrival wave.', action: 'Redirect participants through the north route.', status: 'OPEN' },
]

const times = ['09:15', '09:20', '09:25', '09:30', '09:35', '09:40', '09:45', '09:50', '09:55', '10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30', '10:35', '10:40']
export const demoAnalytics: AnalyticsData = {
  crowd: times.map((time, index) => ({ time, actual: 42 + index * 2.7 + Math.sin(index / 2) * 3, predicted: 44 + index * 2.8 + Math.max(index - 10, 0) * 1.8 })),
  parking: times.map((time, index) => ({ time, actual: 55 + index * 2.2 + Math.sin(index / 3) * 3 })),
  registration: times.map((time, index) => ({ time, teams: Math.round(4 + index * 1.9 + Math.sin(index) * 1.5) })),
  metrics: { total_participants: 1284, total_teams: 50, teams_arrived: 41, teams_checked_in: 34, peak_crowd: 1188, peak_parking: 94, avg_registration: 3.8, avg_wait: 4.6, total_alerts: 18, critical_alerts: 3 },
}
