$xmlPath = Join-Path $env:TEMP "Task.xml"
SCHTASKS /Create /TN "FileSorterNightly" /XML $xmlPath /F
