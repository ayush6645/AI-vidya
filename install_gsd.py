import os
import shutil
import sys
import argparse

def install_gsd(target_dir):
    """Installs the GSD workflow to the target directory."""
    target_dir = os.path.abspath(target_dir)
    agent_dir = os.path.join(target_dir, ".agent")
    workflows_dir = os.path.join(agent_dir, "workflows")
    
    # Source file (assumes script is run from project root or similar, adjusting as needed)
    # In this context, we will write the content directly to avoid path seeking issues if moved
    gsd_content = r'''---
description: Get Shit Done (GSD) - A spec-driven development workflow
---

# Get Shit Done (GSD) Protocol

This workflow implements the **Get Shit Done** philosophy: **Research → Plan → Execute → Verify**.
It is designed to solve context rot and ensure high-quality, verified code output.

## 0. Prerequisite Check
// turbo
1. Check if the `.planning` directory exists.
2. If NOT, suggest running `/gsd-init` first.

## 1. /gsd-init (New Project)
Use this to start a fresh project or milestone.
1.  Create directory `.planning` and `.planning/research`.
2.  **Context Gathering**: Ask the user for:
    - Project Name & One-line vision
    - Core Goals (What does "done" look like?)
    - Technical constraints (Stack, libraries, etc.)
3.  **Artifact Creation**:
    - Create `.planning/PROJECT.md`: Store the vision and goals.
    - Create `.planning/REQUIREMENTS.md`: List detailed requirements (MusS/Should/Could).
    - Create `.planning/ROADMAP.md`: Break work into precise Phases (Phase 1, Phase 2, etc.).
4.  **Handoff**: Present the Roadmap for approval.

## 2. /gsd-plan (Plan Phase)
Use this to plan the next phase of work.
1.  **Context Loading**: Read `.planning/PROJECT.md` and `.planning/ROADMAP.md`.
2.  **Phase selection**: Identify the next active phase.
3.  **Research (Optional)**: If needed, perform web/codebase research to validate technical approach.
4.  **Spec Generation**:
    - Create or Update `implementation_plan.md` (Antigravity's native plan artifact).
    - Map the GSD requirements to specific code changes.
    - **CRITICAL**: The plan MUST include a "Verification Plan" section.
5.  **Review**: Stop and `notify_user` to review the `implementation_plan.md`. Do NOT proceed to execution without approval.

## 3. /gsd-execute (Execute Phase)
Use this to build the approved plan.
1.  **Read Plan**: strict adherence to `implementation_plan.md`.
2.  **Atomic Execution**:
    - Implement features one by one.
    - After each logical unit, run `git commit` (if git is active) or just save.
3.  **Progress Tracking**:
    - Update `.planning/ROADMAP.md` to mark items as `[x]`.
    - Update `task.md` with granular progress.

## 4. /gsd-verify (Verify Work)
Use this to prove it works.
1.  **Verification**: Execute the steps defined in the "Verification Plan" of `implementation_plan.md`.
2.  **Debug**: If verification fails, fix context, plan a fix, and execute.
3.  **Completion**:
    - detailed `walkthrough.md` with proof (logs/screenshots).
    - Update `.planning/ROADMAP.md` (Phase Complete).

## 5. /gsd-status
1.  Read `.planning/ROADMAP.md` and report current status.
'''

    if not os.path.exists(target_dir):
        print(f"Error: Target directory '{target_dir}' does not exist.")
        return

    try:
        os.makedirs(workflows_dir, exist_ok=True)
        target_file = os.path.join(workflows_dir, "get-shit-done.md")
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(gsd_content)
            
        print(f"Successfully installed GSD Workflow to: {target_file}")
        print("You can now use '/gsd-init', '/gsd-plan', etc. in that project.")
        
    except Exception as e:
        print(f"Error installing workflow: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install GSD Workflow to a project.")
    parser.add_argument("target_dir", nargs="?", default=".", help="Target project directory (default: current)")
    args = parser.parse_args()
    
    install_gsd(args.target_dir)
