@echo off
set FILTER_BRANCH_SQUELCH_WARNING=1

cd /d "%~dp0"

echo Cleaning git history...

git filter-branch --force --index-filter "git rm --cached --ignore-unmatch -- 'Mythos Desktop/*' 'Mythos Desktop APp/*'" --prune-empty -- --all

echo Done!
pause
