workflow "New workflow" {
  on = "pull_request_review_comment"
  resolves = ["HTTP client"]
}

action "comment-filter" {
  uses = "actions/bin/filter@master"
  args = "issue_comment lgtm"
}

action "HTTP client" {
  uses = "swinton/httpie.action@master"
  needs = ["comment-filter"]
  args = ["POST", "httpbin.org/anything", "hello=worldx"]
}
