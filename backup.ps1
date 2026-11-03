# ==============================================================================
# Скрипт создания резервной копии ТМ «Сибсыр» (Windows / PowerShell)
# Использование:
#   .\backup.ps1                       - полный бэкап (каталог + фото + заказы + клиенты + статьи)
#   .\backup.ps1 -CatalogOnly          - только каталог с картинками
#   .\backup.ps1 -NoMedia              - только база данных без картинок (легкий дамп)
#   .\backup.ps1 -Stats                - посмотреть текущую статистику
# ==============================================================================

param (
    [switch]$CatalogOnly,
    [switch]$NoMedia,
    [switch]$Stats,
    [string]$Description = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Определение пути к Python
$PythonExe = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonExe = ".\.venv\Scripts\python.exe"
}

if ($Stats) {
    & $PythonExe mysite\manage.py backup_data --stats
    exit $LASTEXITCODE
}

$ArgsList = @("mysite\manage.py", "backup_data")

if ($CatalogOnly) {
    $ArgsList += "-i"
    $ArgsList += "catalog"
}

if ($NoMedia) {
    $ArgsList += "--no-media"
}

if ($Description) {
    $ArgsList += "-d"
    $ArgsList += $Description
}

Write-Host "Запуск создания резервной копии..." -ForegroundColor Cyan
& $PythonExe $ArgsList

