workflow "New workflow" {
  resolves = ["GitHub Action for Slack"]
  on = "pull_request"
}

action "GitHub Action for Slack" {
  uses = "Ilshidur/action-slack@4ab30779c772cac48ffe705d27a5a194e3d5ed78"
  secrets = ["SLACK_WEBHOOK"]
  args = "LGTM!!"
}
