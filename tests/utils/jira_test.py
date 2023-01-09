def test_jira_transition_tickets(jira_obj):
    # Arrange
    jira_instance_obj = jira_obj
    test_issue = jira_instance_obj.jira_obj.create_issue(
        project="PED",
        summary="Test issue for ibs_to_jira script!",
        description="Test issue for ibs_to_jira script!",
        issuetype={"name": "Implementation"},
    )

    # Transition to Effort Estimation
    evaluate_transition_id = jira_instance_obj.jira_get_transition_id(
        test_issue.key, "Evaluate"
    )
    dev_lead_id = jira_instance_obj.jira_get_field_name("Dev Lead")
    fix_version_id = jira_instance_obj.jira_get_field_name("Fix Version/s")
    fix_version_obj = jira_instance_obj.jira_get_version_obj(
        test_issue.key, "15 SP5 GM"
    )
    qe_project_manager_id = jira_instance_obj.jira_get_field_name("QE Project Manager")
    versions = [{"id": version.id} for version in test_issue.fields.fixVersions]
    versions.append({"id": fix_version_obj.id})
    user_obj = jira_instance_obj.jira_obj.search_users(user="eg_admin")[0]
    test_issue.update(
        fields={
            dev_lead_id: user_obj.raw,
            fix_version_id: versions,
            qe_project_manager_id: user_obj.raw,
        }
    )
    jira_instance_obj.jira_obj.transition_issue(
        test_issue.key,
        evaluate_transition_id,
    )

    # Transition to Dev under Estimation
    evaluate_dev_transition_id = jira_instance_obj.jira_get_transition_id(
        test_issue.key, "Evaluate Dev"
    )
    tl_initial_id = jira_instance_obj.jira_get_field_name(
        "TL initial effort estimation"
    )
    tl_ongoing_id = jira_instance_obj.jira_get_field_name(
        "TL ongoing effort estimation"
    )
    test_issue.update(
        fields={
            tl_initial_id: {"value": "No Effort"},
            tl_ongoing_id: {"value": "No Effort"},
        },
    )
    jira_instance_obj.jira_obj.transition_issue(
        test_issue.key,
        evaluate_dev_transition_id,
    )

    # Transition to Ready for Dev
    approve_transition_id = jira_instance_obj.jira_get_transition_id(
        test_issue.key, "Approve"
    )
    jira_instance_obj.jira_obj.transition_issue(test_issue.key, approve_transition_id)

    # Transition to Dev in Progress
    start_transition_id = jira_instance_obj.jira_get_transition_id(
        test_issue.key, "Start"
    )
    jira_instance_obj.jira_obj.transition_issue(test_issue.key, start_transition_id)

    # Transition to Dev Done
    dev_done_transition_id = jira_instance_obj.jira_get_transition_id(
        test_issue.key, "Dev Done"
    )
    jira_instance_obj.jira_obj.transition_issue(test_issue.key, dev_done_transition_id)

    # Act
    jira_instance_obj.jira_transition_tickets(test_issue.key)

    # Assert
    test_issue = jira_instance_obj.jira_obj.issue(test_issue.key)
    assert test_issue.fields.status.name == "QE Open"


def test_jira_do_search(jira_obj):
    # Arrange
    jira_instance = jira_obj()
    jql = "issue = YES-168"

    # Act
    result = jira_instance.jira_do_search(jql)

    # Assert
    assert len(result) == 1
    assert result[0] == "YES-168"
