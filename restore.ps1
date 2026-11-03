# ==============================================================================
# Скрипт восстановления данных ТМ «Сибсыр» (Windows / PowerShell)
# Использование:
#   .\restore.ps1                               - восстановить последний бэкап
#   .\restore.ps1 -Archive "путь_к_файлу.zip"   - восстановить конкретный архив
#   .\restore.ps1 -Clear                        - очистить таблицы перед импортом
#   .\restore.ps1 -DryRun                       - проверить архив без записи в БД
#   .\restore.ps1 -List                         - список всех бэкапов
# ==============================================================================

param (
    [string]$Archive = "",
    [switch]$Clear,
    [switch]$NoMedia,
    [switch]$DryRun,
    [switch]$Yes,
    [switch]$List
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Определение пути к Python
$PythonExe = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonExe = ".\.venv\Scripts\python.exe"
}

if ($List) {
    & $PythonExe mysite\manage.py restore_data --list
    exit $LASTEXITCODE
}

$ArgsList = @("mysite\manage.py", "restore_data")

if ($Archive) {
    $ArgsList += $Archive
}

if ($Clear) {
    $ArgsList += "--clear"
}

if ($NoMedia) {
    $ArgsList += "--no-media"
}

if ($DryRun) {
    $ArgsList += "--dry-run"
}

if ($Yes) {
    $ArgsList += "--yes"
}

Write-Host "Запуск восстановления данных..." -ForegroundColor Cyan
& $PythonExe $ArgsList

