@echo off
set BASE_DIR=%CD%
cd %BASE_DIR%\DockerPythonAgent
call package-agent.bat
cd %BASE_DIR%\DockerCartridge
call ant
cd %BASE_DIR%
