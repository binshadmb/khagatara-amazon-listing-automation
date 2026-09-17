# KHAGATARA Incident Response Plan

**Document owner:** Khagatara Administrator  
**Incident Response Owner / IMPOC:** Khagatara Administrator  
**Review frequency:** At least every 6 months and after a material security incident  
**Version:** 1.0  
**Status:** Active

## 1. Purpose

This plan defines the process used by KHAGATARA to identify, contain, investigate, report, recover from, and learn from security incidents affecting systems, credentials, or Amazon Information used in connection with the Amazon Selling Partner API (SP-API).

The objective is to reduce the impact of incidents, protect Amazon Information, preserve evidence, restore secure operation, and meet applicable Amazon notification and security requirements.

## 2. Scope

This plan applies to:

- KHAGATARA SP-API application code and supporting local systems.
- SP-API credentials, LWA credentials, refresh tokens, access tokens, and other authentication material.
- Amazon Information handled by the application.
- Source code, configuration, logs, backups, and security-related documentation associated with the application.
- Any workstation, server, cloud resource, or third-party service used to operate the SP-API integration.

## 3. Incident Response Owner / IMPOC

**Role:** Khagatara Administrator  
**Responsibility:** The Incident Response Owner / IMPOC coordinates incident response, determines the initial severity, directs containment and recovery, maintains the incident record, and coordinates required external notifications.

If the Incident Response Owner is unavailable, the incident will be handled by the designated account/system administrator until the owner can resume responsibility.

## 4. Security Incident Examples

A security incident may include, but is not limited to:

- Suspected disclosure, theft, or unauthorized use of SP-API or LWA credentials.
- Unauthorized access to Amazon Information.
- Malware, ransomware, or other malicious software affecting a system used by the application.
- Unauthorized modification or deletion of application data or security configuration.
- Compromise of an endpoint, server, cloud resource, or account used by KHAGATARA.
- Accidental publication of credentials or Amazon Information in source control, logs, or another public location.
- Suspicious or unauthorized SP-API activity.
- Loss of a device containing protected credentials or Amazon Information.

## 5. Detection and Initial Assessment

When a suspected incident is identified, the Incident Response Owner will:

1. Record the date and time of detection.
2. Record how the incident was detected and the affected system or account.
3. Determine whether Amazon Information, SP-API credentials, or other protected information may be affected.
4. Identify the systems, accounts, files, and services potentially involved.
5. Assign an initial severity based on the apparent impact and risk.
6. Begin an incident record and preserve relevant evidence.

The initial assessment must not unnecessarily expose credentials or Amazon Information in tickets, logs, screenshots, or source-control commits.

## 6. Containment

The Incident Response Owner will take reasonable steps to stop or limit unauthorized activity. Depending on the incident, containment may include:

- Revoking or rotating affected credentials.
- Disabling compromised accounts or sessions.
- Disconnecting or isolating an affected device or service.
- Blocking unauthorized network access.
- Removing exposed credentials or sensitive information from active systems.
- Temporarily disabling affected application functionality.
- Preserving affected systems and relevant evidence before destructive remediation where practical.

Containment actions must be documented in the incident record.

## 7. Investigation and Evidence Preservation

The Incident Response Owner will preserve available evidence needed to understand the incident and support remediation. Evidence may include:

- Authentication and access records.
- Application and system logs.
- SP-API request identifiers and relevant error responses.
- Git history and repository activity.
- Security alerts.
- File timestamps and relevant system information.
- Records of credential rotation, account changes, and containment actions.

Evidence containing secrets or Amazon Information must be protected and must not be committed to the public source repository.

## 8. Amazon Notification

If a security incident involves Amazon Information or otherwise triggers an applicable Amazon reporting obligation, the Incident Response Owner will follow the applicable Amazon notification requirements.

For an incident requiring notification to Amazon under the applicable SP-API requirements, the incident will be reported to Amazon's designated security contact **within 24 hours of detection**.

The notification will include the information reasonably available at the time, such as:

- Date and time of detection.
- Nature and scope of the incident.
- Systems or Amazon Information potentially affected.
- Known or suspected impact.
- Containment and remediation actions taken.
- Contact information for the Incident Response Owner / IMPOC.
- Additional information requested by Amazon as the investigation progresses.

Follow-up information will be provided as it becomes available and as required by Amazon.

## 9. Eradication and Recovery

After containment, the Incident Response Owner will coordinate removal of the cause of the incident and restoration of secure operation. Actions may include:

- Removing malware or unauthorized software.
- Rotating compromised credentials.
- Correcting vulnerable configuration or code.
- Applying required security updates.
- Restoring affected data from a known-good backup where necessary.
- Validating authentication and authorization controls.
- Testing the affected application before returning it to normal operation.
- Monitoring for recurrence after recovery.

Recovery will not be considered complete until reasonable checks indicate that the identified compromise has been addressed.

## 10. Post-Incident Review

After a material security incident, the Incident Response Owner will document:

- What happened.
- How the incident was detected.
- What information or systems were affected.
- What containment and recovery actions were taken.
- Whether Amazon notification was required and, if so, when it occurred.
- Root cause or contributing factors, where established.
- Corrective actions and responsible owner.
- Lessons learned.

Corrective actions will be tracked until completed.

## 11. Periodic Review

This plan will be reviewed **at least every six months** and additionally after a material security incident, significant system change, or change to applicable Amazon security requirements.

The Incident Response Owner is responsible for completing and documenting the review.

## 12. Incident Record

Each material incident should have a record containing, at minimum:

- Incident identifier.
- Detection date and time.
- Reporter/detection source.
- Incident description.
- Affected systems/accounts.
- Initial severity.
- Containment actions.
- Investigation findings.
- Amazon notification status and timestamp, when applicable.
- Recovery actions.
- Post-incident findings.
- Corrective actions and closure date.

## 13. Security Principles

KHAGATARA will apply the following principles during incident response:

- Protect Amazon Information and credentials from further disclosure.
- Use the minimum necessary access when investigating and containing an incident.
- Preserve evidence where practical.
- Do not place secrets in source control, issue trackers, or public documentation.
- Document significant decisions and actions.
- Escalate promptly when Amazon Information or SP-API credentials may be affected.
- Review and improve controls after significant incidents.

## 14. Approval and Review Record

| Version | Date | Change | Reviewed by |
|---|---|---|---|
| 1.0 | 2026-09-17 | Initial incident response plan | Khagatara Administrator |

