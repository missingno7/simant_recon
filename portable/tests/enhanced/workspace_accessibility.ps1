param([int]$TaskProcess, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$condition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $TaskProcess)
$elements = [System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
$rows = @()
foreach ($element in $elements) {
    $current = $element.Current
    $rows += [pscustomobject]@{
        name=$current.Name; role=$current.ControlType.ProgrammaticName
        hwnd=$current.NativeWindowHandle; keyboard=$current.IsKeyboardFocusable
        patterns=@($element.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName })
    }
}
$passed = @($rows | Where-Object { $_.name -eq 'Go to Yellow Ant' -and $_.keyboard -and $_.patterns -contains 'InvokePatternIdentifiers.Pattern' }).Count -gt 0 -and
    @($rows | Where-Object { $_.name -eq 'Game speed' -and $_.role -eq 'ControlType.ComboBox' }).Count -gt 0
[pscustomobject]@{ passed=$passed; process=$TaskProcess; elements=$rows } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
if (-not $passed) { throw 'Native action-control accessibility coverage missing' }
