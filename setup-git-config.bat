@echo off
REM Apply Git config from .env.git
cd /d "%~dp0"

for /f "tokens=2 delims==" %%a in ('findstr "GIT_USER_NAME" .env.git 2^>nul') do set GIT_USER_NAME=%%a
for /f "tokens=2 delims==" %%a in ('findstr "GIT_USER_EMAIL" .env.git 2^>nul') do set GIT_USER_EMAIL=%%a

set GIT_USER_NAME=%GIT_USER_NAME: =%
set GIT_USER_EMAIL=%GIT_USER_EMAIL: =%

if "%GIT_USER_NAME%"=="" echo Missing GIT_USER_NAME in .env.git & exit /b 1
if "%GIT_USER_EMAIL%"=="" echo Missing GIT_USER_EMAIL in .env.git & exit /b 1

"C:\Program Files\Git\bin\git.exe" config --global user.name "%GIT_USER_NAME%"
"C:\Program Files\Git\bin\git.exe" config --global user.email "%GIT_USER_EMAIL%"

echo Git config set: %GIT_USER_NAME% ^<%GIT_USER_EMAIL%^>
