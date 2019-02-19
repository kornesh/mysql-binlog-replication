workflow "New workflow" {
  on = "pull_request_review_comment"
  resolves = ["GitHub Action for Slack"]
}

action "GitHub Action for Slack" {
  uses = "Ilshidur/action-slack@4ab30779c772cac48ffe705d27a5a194e3d5ed78"
  secrets = ["SLACK_WEBHOOK"]
  args = "LGTM!"
}
