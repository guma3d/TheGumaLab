@echo off
echo Configuring git to use local .githooks directory...
git config core.hooksPath .githooks
echo Done! Please ensure you have Git bash installed for the hooks to run properly.
pause
