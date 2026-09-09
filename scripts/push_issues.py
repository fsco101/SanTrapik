import json
import os
import subprocess
import re

SPRINTS_DIR = os.path.join(os.path.dirname(__file__), "..", "sprints")
SPRINTS_DIR = os.path.abspath(SPRINTS_DIR)

SPRINT_FILES = [
    "sprint-1-data-and-database.json",
    "sprint-2-backend-services.json",
    "sprint-3-frontend-ui.json",
    "sprint-4-ai-ml-prediction.json",
    "sprint-5-integration-testing.json"
]

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Stderr: {result.stderr}")
    return result.stdout.strip()

def ensure_labels(all_labels):
    print(f"Ensuring {len(all_labels)} labels exist on GitHub...")
    for label in all_labels:
        # Default colors
        if label.startswith("sprint-"):
            color = "6366F1"
        elif label in ["high", "critical", "bug"]:
            color = "EF4444"
        elif label in ["frontend", "ui", "design-system"]:
            color = "4CD7F6"
        elif label in ["backend", "fastapi", "api"]:
            color = "10B981"
        elif label in ["database", "postgis", "geospatial"]:
            color = "F59E0B"
        elif label in ["ml", "ai-prediction", "training"]:
            color = "8B5CF6"
        else:
            color = "64748B"
        run_cmd(f'gh label create "{label}" --color "{color}" --force')

def main():
    # 1. Collect all labels
    all_labels = set()
    sprints_data = []
    
    for filename in SPRINT_FILES:
        filepath = os.path.join(SPRINTS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            sprints_data.append((filename, filepath, data))
            for issue in data.get("issues", []):
                for label in issue.get("labels", []):
                    all_labels.add(label)
                if issue.get("priority"):
                    all_labels.add(f"priority:{issue.get('priority')}")
    
    ensure_labels(all_labels)

    # 2. Create issues
    print("\nCreating GitHub issues...")
    for filename, filepath, data in sprints_data:
        sprint_title = data.get("title", filename)
        sprint_id = data.get("sprint_id")
        print(f"\nProcessing {sprint_title}...")
        
        for issue in data.get("issues", []):
            title = issue["title"]
            priority = issue.get("priority", "medium")
            desc = issue.get("description", "")
            criteria = issue.get("acceptance_criteria", [])
            
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
            
            # Extract issue number from output URL (e.g. https://github.com/fsco101/SanTrapik/issues/1)
            match = re.search(r'/issues/(\d+)', out)
            if match:
                issue_num = int(match.group(1))
                issue["github_issue_number"] = issue_num
                issue["github_url"] = out
            
            if os.path.exists(temp_body_path):
                os.remove(temp_body_path)
        
        # Save back updated sprint JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Updated {filename} with issue numbers.")

    print("\nAll GitHub issues created successfully!")

if __name__ == "__main__":
    main()
