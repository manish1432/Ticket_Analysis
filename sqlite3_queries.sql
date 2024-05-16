-- service_issue_distribution
SELECT COUNT(*) FROM ServiceDesk WHERE ServiceIssue = 'Alerts';
SELECT COUNT(*) FROM ServiceDesk WHERE ServiceIssue = 'Request';
SELECT COUNT(*) FROM ServiceDesk WHERE ServiceIssue = 'Self-Ticket';

-- Component-wise
SELECT TriagedBusiness,
    SUM(CASE WHEN ServiceIssue = 'Alerts' THEN 1 ELSE 0 END) AS Alerts_Count,
    SUM(CASE WHEN ServiceIssue = 'Request' THEN 1 ELSE 0 END) AS Request_Count,
    SUM(CASE WHEN ServiceIssue = 'Self-Ticket' THEN 1 ELSE 0 END) AS Self_Ticket_Count
    FROM ServiceDesk
    WHERE TriagedBusiness IN ('The Mill', 'MPC', 'Technicolor Games', 'Mikros Animation')
    GROUP BY TriagedBusiness;

    SELECT Component, COUNT(*) AS Count
FROM ServiceDesk
GROUP BY Component;

-- Engineer-wise
SELECT ServiceIssue, COUNT(*) AS IssueCount
        FROM ServiceDesk
        WHERE Assignee = ?
        GROUP BY ServiceIssue

SELECT ServiceIssue, COUNT(*) AS IssueCount FROM ServiceDesk WHERE Assignee = ? GROUP BY ServiceIssue;

-- BU-wise-tickets
    SELECT
    ServiceIssue,
    COUNT(*) AS IssueCount
FROM
    ServiceDesk
WHERE
    TriagedBusiness = ?
GROUP BY
    ServiceIssue
ORDER BY
    IssueCount DESC;
