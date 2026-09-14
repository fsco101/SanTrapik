import json
import os
import subprocess
import re
import time

SPRINTS_DIR = os.path.join(os.path.dirname(__file__), "..", "sprints")
SPRINTS_DIR = os.path.abspath(SPRINTS_DIR)

SPRINT_FILES = [
    "sprint-1-data-and-database.json",
    "sprint-2-backend-services.json",
    "sprint-3-frontend-ui.json",
    "sprint-4-ai-ml-prediction.json",
    "sprint-5-integration-testing.json",
    "sprint-6-security-consensus.json",
    "sprint-7-realtime-streaming.json",
    "sprint-8-multimodal-manila.json",
    "sprint-9-advanced-ai-forecasting.json",
    "sprint-10-performance-offline-pwa.json"
]

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Stderr: {result.stderr}")
    return result.stdout.strip()

def get_label_color(label: str) -> str:
    if label.startswith("sprint-"):
        return "6366F1"
    if label in ["high", "critical", "bug", "priority:critical", "priority:high"]:
        return "EF4444"
    if label in ["priority:medium"]:
        return "F59E0B"
    if label in ["frontend", "ui", "design-system", "visualization", "react", "tailwind", "ux"]:
        return "4CD7F6"
    if label in ["backend", "fastapi", "api", "middleware", "pubsub", "sse", "streaming"]:
        return "10B981"
    if label in ["database", "postgis", "geospatial", "spatial", "mvt", "redis", "caching", "storage"]:
        return "F59E0B"
    if label in ["ml", "ai-prediction", "training", "mlops", "prediction", "data-science", "uncertainty"]:
        return "8B5CF6"
    if label in ["security", "consensus", "guardrails", "compliance"]:
        return "DC2626"
    if label in ["weather", "hazards", "alerts"]:
        return "EA580C"
    if label in ["motorcycle", "economics", "mmda"]:
        return "0EA5E9"
    if label in ["pwa", "offline", "reliability", "loadtesting", "performance", "qa", "e2e", "devops", "docker", "production"]:
        return "059669"
    return "64748B"

def ensure_labels(all_labels):
    print(f"Ensuring {len(all_labels)} labels exist on GitHub...")
    # Fetch existing labels
    out = run_cmd('gh label list --limit 200 --json name')
    existing_names = set()
    try:
        existing_names = set(l['name'] for l in json.loads(out))
    except Exception:
        pass

    for label in sorted(list(all_labels)):
        if label in existing_names:
            continue
        color = get_label_color(label)
        print(f"Creating label: {label} (#{color})")
        run_cmd(f'gh label create "{label}" --color "{color}" --force')

def get_existing_github_issues():
    out = run_cmd('gh issue list --state all --limit 500 --json number,title,state,url')
    by_title = {}
    try:
        items = json.loads(out)
        for item in items:
            by_title[item["title"].strip()] = item
    except Exception as e:
        print(f"Warning parsing existing issues: {e}")
    return by_title

def main():
    # 1. Collect all labels across all sprints
    all_labels = set()
    sprints_data = []

    for filename in SPRINT_FILES:
        filepath = os.path.join(SPRINTS_DIR, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            sprints_data.append((filename, filepath, data))
            for issue in data.get("issues", []):
                for label in issue.get("labels", []):
                    all_labels.add(label)
                if issue.get("priority"):
                    all_labels.add(f"priority:{issue.get('priority')}")

    ensure_labels(all_labels)

    # 2. Get map of existing GitHub issues
    existing_issues = get_existing_github_issues()
    print(f"\nFound {len(existing_issues)} existing issues on GitHub.")

    # 3. Create or sync issues
    print("\nProcessing GitHub issues...")
    for filename, filepath, data in sprints_data:
        sprint_title = data.get("title", filename)
        sprint_id = data.get("sprint_id")
        sprint_num = data.get("number")
        print(f"\n--- Sprint {sprint_num}: {sprint_title} ---")

        for issue in data.get("issues", []):
            title = issue["title"].strip()
            priority = issue.get("priority", "medium")
            desc = issue.get("description", "")
            criteria = issue.get("acceptance_criteria", [])
            status = issue.get("status", "planned")

            if title in existing_issues:
                gh_info = existing_issues[title]
                issue_num = gh_info["number"]
                issue_url = gh_info.get("url", f"https://github.com/fsco101/SanTrapik/issues/{issue_num}")
                issue["github_issue_number"] = issue_num
                issue["github_url"] = issue_url
                print(f"[EXISTS] #{issue_num}: {title} ({gh_info.get('state')})")
                continue

            body_lines = [
                f"### 🎯 Sprint Association",
                f"**Sprint:** {sprint_title} (`{sprint_id}`)",
                f"**Priority:** `{priority.upper()}`",
                "",
                f"### 📋 Objective & Description",
                desc,
                "",
                f"### ✅ Acceptance Criteria",
            ]
            for ac in criteria:
                body_lines.append(f"- [ ] {ac}")

            body_lines.extend([
                "",
                f"### 📚 Reference Specifications",
                "- [SPEC.md](https://github.com/fsco101/SanTrapik/blob/main/SPEC.md)",
                "- [DESIGN/DESIGN.md](https://github.com/fsco101/SanTrapik/blob/main/DESIGN/DESIGN.md)",
                "- [AGENT.md](https://github.com/fsco101/SanTrapik/blob/main/AGENT.md)"
            ])

            body = "\n".join(body_lines)

            labels = issue.get("labels", []) + [f"priority:{priority}"]
            label_args = " ".join([f'--label "{l}"' for l in labels])

            # Temporary file for body to avoid shell escaping issues on Windows
            temp_body_path = os.path.join(SPRINTS_DIR, "_temp_body.md")
            with open(temp_body_path, "w", encoding="utf-8") as bf:
                bf.write(body)

            cmd = f'gh issue create --title "{title}" --body-file "{temp_body_path}" {label_args}'
            out = run_cmd(cmd)
            print(f"Created: {title} -> {out}")

            # Extract issue number from output URL (e.g. https://github.com/fsco101/SanTrapik/issues/24)
            match = re.search(r'/issues/(\d+)', out)
            if match:
                issue_num = int(match.group(1))
                issue["github_issue_number"] = issue_num
                issue["github_url"] = out
                existing_issues[title] = {"number": issue_num, "url": out, "state": "OPEN"}

                # If the issue is already completed in this sprint, close it with comment
                if status == "completed":
                    close_comment = f"Completed in Sprint {sprint_num}: {sprint_title}"
                    run_cmd(f'gh issue close {issue_num} --comment "{close_comment}"')
                    print(f"Closed #{issue_num} as completed.")

            if os.path.exists(temp_body_path):
                os.remove(temp_body_path)

            time.sleep(1.2)  # Respect API rate limits

        # Save back updated sprint JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Updated {filename} with GitHub references.")

    print("\nAll GitHub issues processed successfully!")

if __name__ == "__main__":
    main()
