/**
 * ULPF File Parser Utility
 * Splits uploaded file content or pasted text into individual log events.
 * Returns an array of raw strings, each representing one event.
 */

/**
 * Main event extraction logic.
 * 1. JSON array -> individual objects.
 * 2. Scans line by line.
 * 3. Handles multi-line JSON objects correctly.
 * 4. Treats any non-empty line as an individual event.
 */
export function extractEvents(content) {
  const events = [];
  const text = content.trim();
  if (!text) return events;

  // 1. Try JSON array first
  if (text.startsWith('[')) {
    try {
      const arr = JSON.parse(text);
      if (Array.isArray(arr)) {
        return arr.map(item => typeof item === 'object' ? JSON.stringify(item) : String(item));
      }
    } catch {
      // Not a valid JSON array, fall through to line-by-line
    }
  }

  // 2. Scan line by line with brace awareness for JSON objects
  const lines = text.split('\n');
  let i = 0;
  while (i < lines.length) {
    let line = lines[i].trim();
    if (!line) {
      i++;
      continue;
    }

    if (line.startsWith('{')) {
      // Attempt to parse as JSON block
      let jsonStr = line;
      let isValid = false;
      try {
        JSON.parse(jsonStr);
        isValid = true;
      } catch (e) {
        // Not valid yet
      }

      if (isValid) {
        events.push(jsonStr);
        i++;
        continue;
      }

      // Try accumulating lines to form a valid JSON object
      let j = i + 1;
      let foundValid = false;
      while (j < lines.length) {
        jsonStr += '\n' + lines[j];
        try {
          JSON.parse(jsonStr);
          foundValid = true;
          break; // Found the end of the JSON object
        } catch (e) {
          j++;
        }
      }

      if (foundValid) {
        events.push(jsonStr);
        i = j + 1;
      } else {
        // If it never formed valid JSON, treat the FIRST line as a regular line
        // and do NOT consume the subsequent lines as part of a malformed JSON.
        events.push(line);
        i++;
      }
    } else {
      // Regular line (Syslog, CEF, unknown, CSV, KeyValue, etc.)
      events.push(line);
      i++;
    }
  }

  return events;
}

/**
 * Parse a .csv file into individual raw event strings.
 * Skips the header row; each data row becomes one event.
 * The event string preserves header=value pairs as key-value text.
 */
function parseCsvFile(content) {
  const lines = content.split('\n').map(l => l.trim()).filter(Boolean);
  if (lines.length <= 1) return lines; // only header or empty

  const headers = lines[0].split(',').map(h => h.trim());
  const events = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    // Build a key=value string so the backend can treat it as key-value log
    const kvPairs = headers.map((h, idx) => `${h}=${values[idx] ?? ''}`).join(' ');
    events.push(kvPairs);
  }

  return events;
}

/**
 * Main entry point. Given file content and extension, returns array of event strings.
 */
export function parseFileIntoEvents(content, extension) {
  const ext = (extension || '').toLowerCase();
  if (ext === '.csv') return parseCsvFile(content);
  // For .txt, .log, .json, and any other text format
  return extractEvents(content);
}

/**
 * Heuristic parsing for pasted text where extension is unknown.
 */
export function parsePastedText(content) {
  return extractEvents(content);
}

/**
 * Returns true if the parsed events array represents multi-event input.
 */
export function isMultiEvent(events) {
  return Array.isArray(events) && events.length > 1;
}
