# Lattice applications: Google Sheet and confirmation email

The application form on `join.html` posts to a small Google Apps Script. For each application it:

1. saves the resume (PDF or Word, up to 10 MB) to a Drive folder called **Lattice resumes**,
2. adds a row to the **Applications** tab of your Google Sheet (with a link to the resume and a `Status` column you can use for review),
3. emails the applicant a branded confirmation, and emails `contact@latryn.com` a copy with links to the resume and the sheet.

It runs on the Google account that owns the sheet. There is no server to host and nothing to pay for.

## Set it up (about ten minutes, once)

1. Sign in to the Google account that should own the applications (ideally the one behind `contact@latryn.com`).
2. Create a new Google Sheet, for example **Latryn Lattice applications**.
3. In the sheet, open **Extensions > Apps Script**. Delete the sample code and paste in all of `lattice-apply.gs`. Check the `CONFIG` block at the top (notification email, reply-to address). Save.
4. In the function menu at the top of the editor choose **setup** and click **Run**. Google asks for permission to use Sheets, Drive and Gmail on your behalf: review and allow. This creates the `Applications` tab and the resumes folder.
5. Click **Deploy > New deployment**. Type: **Web app**. Execute as: **Me**. Who has access: **Anyone**. Click **Deploy** and copy the **Web app URL** (it ends in `/exec`).
6. Paste that URL into `latticeEndpoint` in the `window.LATRYN` block at the top of `assets/site.js` (in both `_source/assets/site.js` and the published `assets/site.js`), commit and publish.
7. Open `https://latryn.com/join.html`, send a test application with your own email, and check that the row, the resume and both emails arrive. Delete the test row afterwards.

Until `latticeEndpoint` is set, the form still validates everything and then opens the applicant's email app with their answers, asking them to attach their resume.

## Changing the script later

Edit the code in the Apps Script editor, then **Deploy > Manage deployments > Edit (pencil) > Version: New version > Deploy**. The URL stays the same, so the website does not need to change. Keep this file in the repo in sync with what is deployed.

If you change any dropdown or checkbox options on the page (`build_pages.py`), change `OPTIONS` in the script too: the script rejects values it does not know.

## Limits and notes

- Gmail sends up to 100 emails a day from a free account and 1,500 from Google Workspace. Each application sends two.
- "Who has access: Anyone" only means anyone can submit to the form. Nobody can read the sheet or the resumes unless you share them.
- The script checks every field again, rejects files that are not `.pdf`, `.doc` or `.docx` or are over 10 MB, and drops submissions that fill the hidden honeypot field.
- Applicants' personal data lives in your Google account. The privacy policy says so; keep it accurate if you move the data elsewhere.
