#!/usr/bin/env bash
set -euo pipefail

REMOTE_URL="https://github.com/Tanglumy/Finance-Bro.git"
TARGET_BRANCH="main"

step(){ echo; echo "==> $*"; }

# 0) 预检：必须在 Git 仓库
step "检查是否在 Git 仓库目录"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "❌ 不在 Git 仓库。请 cd 到 Finance-Bro 根目录再跑"; exit 1; }

# 1) 修复/设置 origin
step "设置远端 origin 为 ${REMOTE_URL}"
if git remote | grep -qx origin; then
  git remote set-url origin "${REMOTE_URL}"
else
  git remote add origin "${REMOTE_URL}"
fi
git remote -v

# 2) 确保当前工作树里不再存在明文 key（先把 CLAUDE.md 改成占位符再提交）
step "确认当前工作区不含 'sk-'；若含，请先在文件里改成占位符再重试"
if git grep -n "sk-[A-Za-z0-9_-]\{8,\}" -- . >/dev/null 2>&1; then
  echo "❌ 仍检测到工作区里有疑似 key，请先手动替换为 \${OPENAI_API_KEY} 并提交。"
  exit 1
fi

step "提交当前改动（若无改动会跳过）"
git add -A || true
git commit -m "Redact API keys in working tree" || echo "（无改动可提交）"

# 3) 准备替换规则（更宽松的正则，覆盖常见 OpenAI key 形态）
step "生成替换规则 replacements.txt"
cat > replacements.txt << 'EOF'
***REMOVED***
regex:sk-[A-Za-z0-9_-]{8,}==>OPENAI_API_KEY_REDACTED
regex:rk-[A-Za-z0-9_-]{8,}==>OPENAI_API_KEY_REDACTED
***REMOVED***
regex:OPENAI_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{8,}==>OPENAI_API_KEY=${OPENAI_API_KEY}
EOF

# 4) 安装并执行 git-filter-repo 进行历史重写（全分支、全标签）
step "运行 git-filter-repo 全库替换（历史重写）"
if ! command -v git-filter-repo >/dev/null 2>&1; then
  python3 -m pip install --user git-filter-repo
fi

# 避免 refs/original 干扰，force 重写
git filter-repo --replace-text replacements.txt --force

# 5) 自检：全历史扫描是否还残留 "sk-"
step "全历史自检：扫描是否还存在 'sk-'"
if git grep -n "sk-[A-Za-z0-9_-]\{8,\}" $(git rev-list --all) -- . >/dev/null 2>&1; then
  echo "⚠️ 仍检测到历史残留 key，进入【兜底方案 A】仅移除 CLAUDE.md 的历史"
  # 兜底 A：把 CLAUDE.md 从整个历史中移除（不影响当前工作树）
  git restore --source=HEAD --worktree --staged -- CLAUDE.md || true
  git filter-repo --path CLAUDE.md --invert-paths --force
  echo "✅ 已移除 CLAUDE.md 的历史版本。"
fi

# 6) 再次自检确认
step "再次全历史扫描"
if git grep -n "sk-[A-Za-z0-9_-]\{8,\}" $(git rev-list --all) -- . >/dev/null 2>&1; then
  echo "❌ 仍有残留：请把报错的 commit 哈希发我，我给你做定点清理。"
  exit 1
fi

# 7) 同步远端并强推
step "fetch 最新远端并强推到 ${TARGET_BRANCH}"
git fetch origin --prune
# 显式推送当前 HEAD 到远端 main
git push origin HEAD:${TARGET_BRANCH} --force -u

echo
echo "✅ 已成功重写历史并推送到 ${REMOTE_URL} (${TARGET_BRANCH})"
echo "⚠️ 别忘了去 OpenAI 控制台 revoke 旧 Key，并把新 Key 只放在 .env / CI Secret 中。"