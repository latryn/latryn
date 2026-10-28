/**
 * Latryn: Lattice application backend (Google Apps Script).
 *
 * Receives the form on join.html, then:
 *   1. saves the resume to a Drive folder,
 *   2. adds one row to the "Applications" tab of the sheet this script is bound to,
 *   3. emails the applicant a confirmation and emails the team a notification.
 *
 * Setup steps are in README.md next to this file. Paste this whole file into
 * Extensions > Apps Script of the Google Sheet that should collect applications.
 */

var CONFIG = {
  notifyEmail: 'contact@latryn.com',   // receives a copy of every application
  replyTo: 'contact@latryn.com',       // where applicants' replies go
  senderName: 'Latryn',
  sheetName: 'Applications',
  folderName: 'Lattice resumes',       // created in your Drive on the first application
  siteUrl: 'https://latryn.com'
};

var OPTIONS = {
  qualification: ['Diploma', 'Bachelors', 'Masters', 'PhD'],
  stream: ['Science', 'Commerce', 'Arts', 'Engineering', 'Other'],
  specialization: [
    'Physical Sciences (Physics, Chemistry, Astronomy, Earth Sciences)',
    'Life Sciences (Biology, Zoology, Botany, Genetics, Ecology)',
    'Health & Medical Sciences (Medicine, Nursing, Pharmacology, Neuroscience)',
    'Computing & Data (Computer Science, Data Analytics, AI, Cloud Computing)',
    'Development & Networks (Software Engineering, Web Development, Cybersecurity, Network Administration)',
    'Core Engineering (Mechanical, Electrical, Civil, Chemical)',
    'Advanced Engineering (Aerospace, Biomedical, Environmental, Robotics)',
    'Visual Arts (Graphic Design, Fine Arts, Painting, Photography, Sculpture)',
    'Media & Digital Arts (Animation, UI/UX Design, Game Design, Video Production, Digital Illustration)',
    'Performing Arts (Music Production, Sound Design, Theater, Choreography)',
    'Design & Architecture (Industrial Design, Fashion Design, Urban Planning, Architecture)',
    'Humanities & Communication (Technical Writing, Ethics in Technology, Language Arts, History)',
    'Pure Mathematics (Algebra, Calculus, Geometry, Number Theory)',
    'Applied Mathematics (Statistics, Actuarial Science, Cryptography, Quantitative Finance)',
    'Other'
  ],
  workTypes: ['Writing / Content', 'Design', 'Development', 'Data / Research', 'Teaching / Tutoring', 'Other'],
  availability: ['Part-time', 'Full-time', 'Weekends only']
};

var HEADERS = ['Submitted at', 'Application ID', 'First name', 'Last name', 'Email', 'Phone number',
  'Qualification', 'Stream', 'Specialization', 'Type of freelance work', 'Availability',
  'Portfolio / LinkedIn', 'Role of interest', 'Resume', 'Status'];

var MAX_BYTES = 10 * 1024 * 1024;
var RESUME_TYPES = {
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
};

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    var d = JSON.parse(e.postData.contents);
    if (d.website) return reply({ ok: true });           // honeypot: bots fill the hidden field
    var a = clean(d);
    lock.waitLock(30000);
    var id = 'LAT-' + Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyMMdd') + '-' + Utilities.getUuid().slice(0, 6).toUpperCase();
    var resume = saveResume(d.resume, a, id);
    sheet().appendRow([
      new Date(), id, a.firstName, a.lastName, a.email, "'" + a.phone,
      a.qualification, a.stream, a.specialization, a.workTypes.join(', '), a.availability,
      a.portfolio, a.role, resume.getUrl(), 'New'
    ].map(safe));
    lock.releaseLock();
    confirmApplicant(a, id);
    notifyTeam(a, id, resume);
    return reply({ ok: true, id: id });
  } catch (err) {
    console.error(err);
    return reply({ ok: false, error: err.userMessage || 'Something went wrong on our side' });
  } finally {
    try { lock.releaseLock(); } catch (ignore) {}
  }
}

/* A GET on the web app URL is a quick way to check the deployment is live. */
function doGet() { return reply({ ok: true, service: 'Latryn Lattice applications' }); }

function clean(d) {
  function str(k, max, required) {
    var v = String(d[k] == null ? '' : d[k]).trim().slice(0, max);
    if (required && !v) fail('Missing ' + k);
    return v;
  }
  function pick(k) {
    var v = str(k, 200, true);
    if (OPTIONS[k].indexOf(v) < 0) fail('Choose a valid ' + k);
    return v;
  }
  var a = {
    firstName: str('firstName', 80, true),
    lastName: str('lastName', 80, true),
    email: str('email', 160, true).toLowerCase(),
    phone: str('phone', 20, true),
    qualification: pick('qualification'),
    stream: pick('stream'),
    specialization: pick('specialization'),
    availability: pick('availability'),
    portfolio: str('portfolio', 300, false),
    role: str('role', 80, false)
  };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(a.email)) fail('Enter a valid email address');
  if (!/^[0-9]{10}$/.test(a.phone)) fail('Enter a 10-digit phone number');
  if (a.portfolio && !/^https?:\/\/\S+$/i.test(a.portfolio)) fail('Enter a full portfolio link starting with https://');
  a.workTypes = (Array.isArray(d.workTypes) ? d.workTypes : []).filter(function (w) { return OPTIONS.workTypes.indexOf(w) >= 0; });
  if (!a.workTypes.length) fail('Choose at least one type of work');
  return a;
}

function saveResume(r, a, id) {
  if (!r || !r.data || !r.name) fail('Upload your resume');
  var ext = String(r.name).split('.').pop().toLowerCase();
  if (!RESUME_TYPES[ext]) fail('Upload a PDF or Word document');
  var bytes = Utilities.base64Decode(r.data);
  if (bytes.length > MAX_BYTES) fail('The resume is larger than 10 MB');
  var name = [id, a.firstName, a.lastName].join(' ').replace(/[^\w .-]+/g, '').trim() + '.' + ext;
  var file = folder().createFile(Utilities.newBlob(bytes, RESUME_TYPES[ext], name));
  file.setDescription('Lattice application ' + id + ' from ' + a.email);
  return file;
}

function sheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(CONFIG.sheetName) || ss.insertSheet(CONFIG.sheetName);
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
    sh.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold').setBackground('#110f0c').setFontColor('#f5f2ec');
    sh.setFrozenRows(1);
  }
  return sh;
}

function folder() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('FOLDER_ID');
  if (id) { try { return DriveApp.getFolderById(id); } catch (gone) {} }
  var f = DriveApp.createFolder(CONFIG.folderName);
  props.setProperty('FOLDER_ID', f.getId());
  return f;
}

function confirmApplicant(a, id) {
  var body =
    p('Hi ' + esc(a.firstName) + ',') +
    p('Thanks for applying to the Lattice, the Latryn network of engineers, researchers and specialists. We have your application and resume.') +
    p('<b>What happens next.</b> Our team reads every application. If your background fits a current program, we will email you a two-part timed assessment: an auto-scored technical section and a scenario section reviewed by our team.') +
    summary(a, id) +
    p('If anything above is wrong, reply to this email and we will update it.') +
    p('The Latryn team');
  MailApp.sendEmail({
    to: a.email,
    subject: 'We received your Lattice application (' + id + ')',
    htmlBody: layout('Application received', body),
    body: 'Hi ' + a.firstName + ',\n\nThanks for applying to the Lattice. We have your application (' + id + ') and resume. ' +
      'If your background fits a current program, we will email you the assessment.\n\nThe Latryn team\n' + CONFIG.siteUrl,
    name: CONFIG.senderName,
    replyTo: CONFIG.replyTo
  });
}

function notifyTeam(a, id, resume) {
  var body = p('New Lattice application from <b>' + esc(a.firstName + ' ' + a.lastName) + '</b>.') + summary(a, id) +
    p('<a href="' + resume.getUrl() + '" style="color:#056e5b">Open resume</a> &nbsp; <a href="' + SpreadsheetApp.getActiveSpreadsheet().getUrl() + '" style="color:#056e5b">Open sheet</a>');
  MailApp.sendEmail({
    to: CONFIG.notifyEmail,
    subject: 'Lattice application | ' + a.specialization.split(' (')[0] + ' | ' + a.firstName + ' ' + a.lastName,
    htmlBody: layout('New application', body),
    name: 'Latryn website',
    replyTo: a.email
  });
}

function summary(a, id) {
  var rows = [['Application ID', id], ['Name', a.firstName + ' ' + a.lastName], ['Email', a.email], ['Phone', a.phone],
    ['Qualification', a.qualification], ['Stream', a.stream], ['Specialization', a.specialization],
    ['Type of work', a.workTypes.join(', ')], ['Availability', a.availability]];
  if (a.portfolio) rows.push(['Portfolio', a.portfolio]);
  if (a.role) rows.push(['Role of interest', a.role]);
  return '<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin:8px 0 20px;font-size:14px">' +
    rows.map(function (r) {
      return '<tr><td style="padding:9px 12px 9px 0;border-bottom:1px solid #d7d4cd;color:#66635e;font-family:Menlo,monospace;font-size:12px;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;vertical-align:top">' + r[0] +
        '</td><td style="padding:9px 0;border-bottom:1px solid #d7d4cd;color:#110f0c">' + esc(r[1]) + '</td></tr>';
    }).join('') + '</table>';
}

/* Brand layout: stone ground, ink text, verdigris rule, the ember square as the full stop. */
function layout(title, inner) {
  return '<div style="background:#f5f2ec;padding:32px 16px;font-family:Helvetica,Arial,sans-serif">' +
    '<div style="max-width:560px;margin:0 auto;background:#fbfaf7;border:1px solid #d7d4cd;border-radius:16px;overflow:hidden">' +
    '<div style="height:4px;background:#056e5b"></div>' +
    '<div style="padding:32px">' +
    '<div style="font-size:26px;font-weight:700;letter-spacing:-.5px;color:#110f0c">latryn<span style="display:inline-block;width:6px;height:6px;background:#be4100;margin-left:2px"></span></div>' +
    '<h1 style="font-size:22px;line-height:1.25;margin:24px 0 16px;color:#110f0c">' + title + '<span style="display:inline-block;width:5px;height:5px;background:#be4100;margin-left:3px"></span></h1>' +
    '<div style="font-size:15px;line-height:1.6;color:#2f2e2a">' + inner + '</div></div>' +
    '<div style="padding:18px 32px;border-top:1px solid #d7d4cd;font-size:12px;color:#66635e">Latryn, Bengaluru, India &nbsp;·&nbsp; <a href="' + CONFIG.siteUrl + '" style="color:#056e5b">latryn.com</a></div>' +
    '</div></div>';
}

function p(html) { return '<p style="margin:0 0 14px">' + html + '</p>'; }
function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
/* stop a value like "=IMPORTXML(...)" from running as a formula in the sheet */
function safe(v) { return typeof v === 'string' && /^[=+\-@]/.test(v) ? "'" + v : v; }
function fail(msg) { var e = new Error(msg); e.userMessage = msg; throw e; }
function reply(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }

/* Run once from the editor to grant permissions and create the sheet tab and Drive folder. */
function setup() {
  sheet();
  folder();
  console.log('Ready. Resumes folder: ' + folder().getUrl());
}
