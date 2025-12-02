/**
 * Convert 24-hour time format (HH:MM:SS or HH:MM) to 12-hour format with AM/PM
 * @param {string} time24 - Time in 24-hour format (e.g., "14:30:00" or "14:30")
 * @returns {string} Time in 12-hour format (e.g., "2:30 PM")
 */
export function convertTo12Hour(time24) {
  if (!time24) return '';
  
  try {
    // Split the time string
    const parts = time24.split(':');
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1];
    
    // Determine AM/PM
    const period = hours >= 12 ? 'PM' : 'AM';
    
    // Convert to 12-hour format
    if (hours === 0) {
      hours = 12; // Midnight
    } else if (hours > 12) {
      hours = hours - 12;
    }
    
    return `${hours}:${minutes} ${period}`;
  } catch (error) {
    console.error('Error converting time:', error);
    return time24; // Return original if conversion fails
  }
}
