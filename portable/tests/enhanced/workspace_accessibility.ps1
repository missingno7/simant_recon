param([int]$TaskProcess, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$condition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $TaskProcess)
$nameCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, 'SimAnt - Native Workspace Preview')
$both = New-Object System.Windows.Automation.AndCondition($condition, $nameCondition)
$root = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Children, $both)
if ($null -eq $root) { throw 'Workspace process has no accessible native root' }
$elements = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
$rows = @()
foreach ($element in $elements) {
    $current = $element.Current
    $rows += [pscustomobject]@{
        name = $current.Name; role = $current.ControlType.ProgrammaticName
        hwnd = $current.NativeWindowHandle; keyboard = $current.IsKeyboardFocusable
        patterns = @($element.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName })
    }
}
$passed = @($rows | Where-Object { $_.name -like 'World.*' -and $_.keyboard }).Count -gt 0 -and
    @($rows | Where-Object { $_.role -eq 'ControlType.TabItem' }).Count -gt 0 -and
    @($rows | Where-Object { $_.role -eq 'ControlType.Slider' }).Count -gt 0 -and
    @($rows | Where-Object { $_.name -eq 'Move panel' -and $_.patterns -contains 'InvokePatternIdentifiers.Pattern' }).Count -gt 0
[pscustomobject]@{ passed=$passed; root=$root.Current.Name; elements=$rows } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
if (-not $passed) { throw 'Native control accessibility coverage missing' }
