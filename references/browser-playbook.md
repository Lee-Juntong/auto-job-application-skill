# Browser application playbook

## General form loop

1. Claim or open the authenticated tab.
2. Read the current URL and visible DOM.
3. Fill one logical section at a time.
4. Re-read the DOM after uploads, dropdown selections, validation, navigation, or modal changes.
5. Verify selected values rather than trusting typed autocomplete text.
6. Review the complete form against the approved packet.
7. Submit once and wait for authoritative confirmation.

Dynamic forms invalidate locators after state changes. Rebuild locators from a fresh snapshot instead of retrying stale nodes.

## Uploads

- Prefer the visible `Attach`, `Upload`, or `Choose file` control.
- Start the file-chooser wait before clicking the upload control.
- Set the absolute local file path on the chooser.
- Verify the displayed employer-facing filename after upload.
- Do not upload hidden supporting documents merely because a file field exists; confirm the field's purpose.

On dynamic Greenhouse forms, a direct `input[type=file]` click may time out. Use the current visible `Attach` control with the file-chooser event.

## Dropdowns and phone fields

- Select exact visible options for country, work authorization, degree, and demographic fields.
- For international phone controls, verify that the country code remains displayed after selection.
- If a dropdown has no truthful option, stop instead of choosing the closest misleading answer.

## Accounts and authentication

- Reuse an authenticated session when available.
- Create an account only when the user authorized account creation for applications.
- Prefer passwordless email-code sign-in when offered.
- Stop for email codes, MFA, CAPTCHAs, identity verification, or authenticator prompts.
- Record only platform, email, and authentication method in a local-only registry. Never expose or commit passwords.

## Platform notes

- **Greenhouse:** Expect dynamic sections and file-chooser uploads. Verify phone country code and confirmation page.
- **Workday:** Sessions expire often. Reauthenticate, use parsed resume data only as a draft, and review every imported field.
- **Eightfold:** Resume parsing can populate demographic and legal fields incorrectly; verify them explicitly.
- **SmartRecruiters:** Recheck screening pages after sign-in and before final submission.
- **JobStreet/SEEK:** Profile imports can create duplicate entries. Review the final application summary; the summary's role and qualification counts are stronger evidence than transient import cards.
- **ByteDance/TikTok:** Application quotas are material. Verify remaining quota, referral code, resume, education dates, and final receipt; slider CAPTCHA requires user action.
- **LinkedIn:** Confirm the company and role in the final review because Easy Apply modals can retain prior answers.

## Confirmation hierarchy

Strong evidence, from best to weaker:

1. Confirmation number or application-history entry for the exact role.
2. Success URL plus explicit receipt text naming the employer or role.
3. Success modal plus stable submitted state.

Not evidence: a click, disabled button, spinner, network silence, or returning to a careers home page.

Record the exact text and URL immediately because application state and sessions are perishable.
