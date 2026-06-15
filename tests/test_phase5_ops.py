"""Tests for the operations agents: security, deployment, github backup, dns, social, analytics."""

from agents.analytics_agent import AnalyticsAgent
from agents.deployment_agent import DeploymentAgent
from agents.dns_website_agent import DnsWebsiteAgent
from agents.github_backup_agent import GitHubBackupAgent
from agents.security_agent import SEVERITY_OK, SecurityAgent
from agents.social_publishing_agent import SocialPublishingAgent


def test_security_env_is_gitignored():
    findings = SecurityAgent().scan()
    env = next(f for f in findings if f.check == "env_gitignored")
    assert env.severity == SEVERITY_OK
    assert "Security scan" in SecurityAgent().report()


def test_deployment_checklist_and_next_credential():
    da = DeploymentAgent()
    assert da.checklist()
    assert da.next_missing_credential(set()).startswith("I need")
    have_all = {k for k, _ in da.required_credentials()}
    assert da.next_missing_credential(have_all) is None


def test_github_backup_protects_secrets():
    g = GitHubBackupAgent()
    s = g.safety_check()
    assert s["gitignore_protects_secrets"] is True   # .env / *.key / *.pem are ignored
    assert g.backup_commands()[0] == "git add -A"


def test_dns_records_and_instructions():
    d = DnsWebsiteAgent()
    recs = d.required_records("1.2.3.4")
    assert any(r["value"] == "1.2.3.4" for r in recs)
    assert "sportsversenews.com" in d.instructions("1.2.3.4")


def test_social_prepares_but_never_posts(tmp_path):
    s = SocialPublishingAgent(posts_log=tmp_path / "posts.jsonl")
    post = s.prepare("hello fans", "tiktok", title="Clip")
    assert post["status"] == "prepared"
    assert s.publish(post, approved=False)["status"] == "not_published"
    assert s.publish(post, approved=True, live_capability=False)["status"] == "not_published"
    # Even with approval AND a (hypothetical) live capability, there is no executor (Phase 5).
    assert s.publish(post, approved=True, live_capability=True)["status"] == "not_published"


def test_analytics_record_and_summarize(tmp_path):
    a = AnalyticsAgent(store_path=tmp_path / "m.jsonl")
    a.record_metrics("c1", "tiktok", {"views": 1000, "likes": 100, "comments": 20})
    a.record_metrics("c2", "youtube", {"views": 50, "likes": 2, "comments": 0})
    s = a.summarize()
    assert s["count"] == 2
    assert s["best"]["content_id"] == "c1"
    assert s["worst"]["content_id"] == "c2"
