/**
 * Crooked Ideas dashboard — Gmail forwarder.
 *
 * Runs in Google Apps Script on a daily trigger. It looks for an unprocessed
 * Weekly Social Analytics email, posts its subject and plain-text body to this
 * repository as a repository_dispatch event, and labels the thread so the same
 * email is never sent twice. The GitHub Action does the parsing.
 *
 * Setup is in the README under "Automating the weekly email".
 */

const CONFIG = {
  owner: 'readchaoticera',
  repo: 'ideas-social-analytics',
  eventType: 'weekly-analytics',

  // Gmail search for the weekly email. Subjects have varied over time
  // ("Weekly Social Analytics", "Social Weekly Analytics", "Weekly Social
  // Report"), so this matches on the words rather than an exact phrase.
  query: 'subject:(social (analytics OR report)) newer_than:14d',

  // Applied once an email has been sent, so re-runs skip it.
  processedLabel: 'Ideas dashboard synced',

  // The body must mention this, or it is not the email we want.
  requiredText: 'Crooked Ideas',

  // A normal week is a few KB. Anything far larger means we picked up the
  // wrong message, and repository_dispatch payloads are size-limited.
  maxBodyChars: 60000,
};

function syncWeeklyAnalytics() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) throw new Error('Set the GITHUB_TOKEN script property first.');

  const label = getOrCreateLabel_(CONFIG.processedLabel);
  const threads = GmailApp.search(CONFIG.query + ' -label:"' + CONFIG.processedLabel + '"');
  if (!threads.length) {
    console.log('No unprocessed weekly email found.');
    return;
  }

  let sent = 0;
  threads.forEach(function (thread) {
    const messages = thread.getMessages();
    // Oldest first, so a thread carrying several weeks goes in order.
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];
      const subject = message.getSubject();
      const body = message.getPlainBody();

      if (body.indexOf(CONFIG.requiredText) === -1) {
        console.log('Skipping (no ' + CONFIG.requiredText + ' section): ' + subject);
        continue;
      }
      if (body.length > CONFIG.maxBodyChars) {
        console.log('Skipping (body is ' + body.length + ' chars): ' + subject);
        continue;
      }

      dispatch_(token, subject, body);
      console.log('Sent: ' + subject);
      sent++;
    }
    thread.addLabel(label);
  });

  console.log('Dispatched ' + sent + ' email(s).');
}

function dispatch_(token, subject, body) {
  const url = 'https://api.github.com/repos/' + CONFIG.owner + '/' + CONFIG.repo + '/dispatches';
  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
    },
    payload: JSON.stringify({
      event_type: CONFIG.eventType,
      client_payload: { subject: subject, body: body },
    }),
    muteHttpExceptions: true,
  });

  const code = response.getResponseCode();
  if (code !== 204) {
    throw new Error('GitHub returned ' + code + ': ' + response.getContentText());
  }
}

function getOrCreateLabel_(name) {
  return GmailApp.getUserLabelByName(name) || GmailApp.createLabel(name);
}

/** Run once from the editor to create the daily trigger. */
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncWeeklyAnalytics') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncWeeklyAnalytics').timeBased().everyDays(1).atHour(14).create();
  console.log('Daily trigger installed (about 2pm in the script time zone).');
}

/** Run once to check the search finds the right email, sending nothing. */
function previewMatches() {
  const threads = GmailApp.search(CONFIG.query);
  console.log('Matched ' + threads.length + ' thread(s):');
  threads.forEach(function (thread) {
    thread.getMessages().forEach(function (m) {
      const body = m.getPlainBody();
      console.log('  ' + m.getDate().toDateString() + ' — ' + m.getSubject() +
        ' [' + body.length + ' chars, Crooked Ideas section: ' +
        (body.indexOf(CONFIG.requiredText) > -1) + ']');
    });
  });
}
