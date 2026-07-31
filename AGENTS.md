# Worktree Policy

When starting any new feature or fix, begin by creating a separate git worktree from the base branch and do all work inside it, so parallel agents never overwrite each other's changes. After the work is merged, clean up by removing the worktree. For the next task, create a fresh worktree from the latest base branch—don't reuse old trees.
