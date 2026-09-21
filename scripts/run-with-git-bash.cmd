@echo off
setlocal

set "bash_exe="

for /f "delims=" %%I in ('where git 2^>NUL') do (
    if exist "%%~dpI..\bin\bash.exe" (
        set "bash_exe=%%~dpI..\bin\bash.exe"
        goto :found_bash
    )
)

echo Could not locate Git for Windows Bash ("..\bin\bash.exe" relative to git on PATH). Ensure Git for Windows is installed and that git and bash.exe are available on PATH.
exit /b 1

:found_bash
echo Detected Windows - using Git Bash...
rem When launched from PowerShell/cmd, bash.exe may inherit a PATH that does
rem not contain Git's POSIX utilities (dirname, awk, sed, etc.). Add the
rem corresponding Git directories explicitly so repository shell scripts work
rem independently of the caller's PATH.
for %%B in ("%bash_exe%") do set "git_root=%%~dpB.."
set "PATH=%git_root%\usr\bin;%git_root%\mingw64\bin;%PATH%"
"%bash_exe%" --login %*
set "cmd_rc=%ERRORLEVEL%"
exit /b %cmd_rc%
